import argparse
import os
import textwrap
from pathlib import Path
from graphviz import Digraph
from sqlmodel import select

from hazy_oracles_user_study.database import (
    DatabaseManager,
    ConversationRoot,
    SampleResponse,
    SAMPLE_TYPE
)

def visualize_tree(session, root: ConversationRoot, output_dir: Path):
    """
    Generates a visual flow diagram of the conversation tree using Graphviz.
    """
    
    # Create the directed graph
    dot = Digraph(name=f'DialogTree_{root.root_id}', comment='Dialog Tree Visualization')
    dot.attr(rankdir='LR')  # Left to Right layout
    dot.attr('node', shape='plaintext') # Use plaintext so our HTML tables define the shape
    
    # Distinct colors for roles
    colors = {
        "ROOT": "#E0F7FA",                   # Cyan-ish
        SAMPLE_TYPE.ASKER: "#FFF3E0",        # Orange-ish (Assistant)
        SAMPLE_TYPE.ANSWERER: "#E0F7FA",     # Cyan-ish (User)
        SAMPLE_TYPE.SKIP: "#F5F5F5",         # Light Gray
        "INFERENCE": "#E8F5E9"               # Green-ish (Final Guess)
    }

    # 1. Prepare Root Node HTML
    img_html = ""
    if root.multimodal_file_path:
        img_path = Path(root.multimodal_file_path)
        if img_path.exists():
            img_fpath = img_path.absolute().as_posix()
            img_html = f'<tr><td><img src="{img_fpath}" scale="true" width="150"/></td></tr>'

    display_text = textwrap.fill(root.ambiguous_question, width=50)
    display_text = display_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    display_text = display_text.replace("\n", "<br/>")

    header_color = "#333333"
    bg_color = colors["ROOT"]
    meta_color = "#eeeeee"

    additional_rows = f"""
    <tr><td bgcolor="{meta_color}">Unambiguous Q: {textwrap.fill(root.unambiguous_question, width=50).replace("\n", "<br/>")}</td></tr>
    <tr><td bgcolor="{meta_color}">Original Dataset: {root.original_dataset} (ID: {root.original_dataset_sample_id})</td></tr>
    """

    label = f'''<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="{bg_color}">
        <tr><td bgcolor="{header_color}"><font color="white"><b>Root</b></font></td></tr>
        {img_html}
        <tr><td>{display_text}</td></tr>
        {additional_rows}
    </table>>'''

    dot.node(root.root_id, label=label)

    # 2. Query and Add Sample Nodes
    statement = select(SampleResponse).where(SampleResponse.root_id == root.root_id)
    samples: list[SampleResponse] = session.exec(statement).all()

    # First pass adds all nodes
    for sample in samples:
        meta_text = ""
        
        if sample.sample_type == SAMPLE_TYPE.ASKER:
            node_type_name = "Asker"
            raw_display_text = sample.next_question if sample.next_question else "No question provided"
            
            if sample.previous_answer_meaningful_score is not None:
                meta_text += f"Prev Ans Meaningful: {sample.previous_answer_meaningful_score:.2f}<br/>"

        elif sample.sample_type == SAMPLE_TYPE.ANSWERER:
            node_type_name = "Answerer"
            raw_display_text = sample.answer if sample.answer else "No answer provided"
            
            if sample.previous_question_relevant_score is not None:
                meta_text += f"Prev Q Relevant: {sample.previous_question_relevant_score:.2f}<br/>"
                
        elif sample.sample_type == SAMPLE_TYPE.SKIP:
            node_type_name = "Skip"
            raw_display_text = "Skipped"
        else:
            node_type_name = "Unknown"
            raw_display_text = ""

        # Format display text
        display_text = textwrap.fill(raw_display_text, width=50)
        display_text = display_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        display_text = display_text.replace("\n", "<br/>")

        # Determine color
        bg_color = colors.get(sample.sample_type, "#FFFFFF")

        # Construct Label
        label = f'''<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="{bg_color}">
            <tr><td bgcolor="{header_color}"><font color="white"><b>{node_type_name} ({sample.node_code})</b></font></td></tr>
            <tr><td>{display_text}</td></tr>
            {f'<tr><td bgcolor="{meta_color}">{meta_text}</td></tr>' if meta_text else ""}
            <tr><td bgcolor="{meta_color}"><font point-size="10">ID: {sample.sample_id[:8]}... | Participant: {sample.participant_type}</font></td></tr>
        </table>>'''

        dot.node(sample.sample_id, label=label)

        if sample.current_guess is not None:
            guess_node_id = f"{sample.sample_id}_guess"
            guess_meta_text = ""
            if sample.current_guess_confidence_score is not None:
                guess_meta_text += f"Guess Conf: {sample.current_guess_confidence_score:.2f}<br/>"
            
            guess_raw_text = f"Guess: {sample.current_guess}"
            guess_display_text = textwrap.fill(guess_raw_text, width=50)
            guess_display_text = guess_display_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            guess_display_text = guess_display_text.replace("\n", "<br/>")
            
            guess_bg_color = colors["INFERENCE"]
            guess_label = f'''<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" bgcolor="{guess_bg_color}">
                <tr><td bgcolor="{header_color}"><font color="white"><b>Inference</b></font></td></tr>
                <tr><td>{guess_display_text}</td></tr>
                {f'<tr><td bgcolor="{meta_color}">{guess_meta_text}</td></tr>' if guess_meta_text else ""}
            </table>>'''
            
            dot.node(guess_node_id, label=guess_label)
            dot.edge(sample.sample_id, guess_node_id)

    # Second pass adds all the edges
    for sample in samples:
        if sample.parent_sample_id is None:
            dot.edge(root.root_id, sample.sample_id)
        else:
            dot.edge(sample.parent_sample_id, sample.sample_id)

    # Render
    try:
        output_path = dot.render(root.root_id, directory=output_dir, format='png', view=False)
        print(f"Visualization saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error rendering Graphviz for root {root.root_id}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Visualize conversation trees from the database.")
    parser.add_argument("db_path", type=str, help="Path to the SQLite database.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Visualize all trees in the database.")
    group.add_argument("--root-id", type=str, help="Visualize a specific tree by root ID.")
    
    parser.add_argument("--out-dir", type=str, default="./tree_visualizations", help="Output directory for visualizations.")
    
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Add sqlite:/// prefix if missing for sqlmodel
    db_url = args.db_path
    if not db_url.startswith("sqlite:///"):
        db_url = f"sqlite:///{Path(db_url).absolute()}"
        
    db_manager = DatabaseManager(db_url)
    
    # We use next() because get_session yields the session
    session_generator = db_manager.get_session()
    session = next(session_generator)
    
    try:
        if args.all:
            roots = session.exec(select(ConversationRoot)).all()
            if not roots:
                print("No roots found in the database.")
            for root in roots:
                print(f"Visualizing tree for root: {root.root_id}")
                visualize_tree(session, root, out_dir)
        else:
            root = session.get(ConversationRoot, args.root_id)
            if not root:
                print(f"Error: Root with ID '{args.root_id}' not found.")
                return
            print(f"Visualizing tree for root: {root.root_id}")
            visualize_tree(session, root, out_dir)
    finally:
        session.close()

if __name__ == "__main__":
    main()
