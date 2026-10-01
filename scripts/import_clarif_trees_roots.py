import argparse
from pathlib import Path
from pydantic import BaseModel
import shutil
import json

from hazy_oracles_user_study.database import ConversationRoot
from hazy_oracles_user_study.utils import generate_uuid

class ClarifTreeDataSchema(BaseModel):
    root_id: str
    ambiguous_question: str
    priority: float
    unambiguous_question: str
    gold_answer: str
    answers: list[str]
    multimodal_file_path: str
    original_dataset: str
    original_dataset_sample_id: str

def main():
    parser = argparse.ArgumentParser(description="Import ClarifTrees conversation roots.")
    parser.add_argument(
        "--chosen-samples-paths",
        type=Path,
        nargs="+",
        default=[Path("/Users/aidan/Downloads/chosen_samples")],
        help="Path(s) to the chosen samples directories."
    )
    parser.add_argument(
        "--max-roots",
        type=int,
        default=None,
        help="Maximum number of conversation roots to import, keeping the highest priority ones."
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite local data without prompting."
    )
    args = parser.parse_args()

    for p in args.chosen_samples_paths:
        if not p.exists():
            print(f"Error: Chosen samples path {p} does not exist.")
            exit(1)

    local_roots_path = Path(__file__).parent.parent / "data" / "conversation_roots" / "clarif_trees"
    local_roots_path.mkdir(parents=True, exist_ok=True)
    local_roots_image_dir = local_roots_path / "images"
    local_roots_image_dir.mkdir(parents=True, exist_ok=True)
    local_roots_data_path = local_roots_path / "roots.json"

    if local_roots_data_path.exists() and not args.force:
        print(f"Local data found at {local_roots_data_path}. Do you want to overwrite it?")
        print("c to continue, anything else to exit")
        response = input()
        if response != "c":
            exit(0)
        print("Continuing...")

    parsed_samples = []

    for chosen_samples_path in args.chosen_samples_paths:
        for sample_path in chosen_samples_path.iterdir():
            if not sample_path.is_dir():
                continue

            sample_data_path = sample_path / "data.json"
            
            if not sample_data_path.exists():
                continue

            with sample_data_path.open("r") as f:
                sample_data_raw = json.load(f)
            sample_data = ClarifTreeDataSchema.model_validate(sample_data_raw)

            sample_img_path = Path(sample_data.multimodal_file_path)
            if not sample_img_path.exists():
                # Try to recover by looking for sample_path / {root_id}.jpg
                recovered_sample_img_path = sample_path / f"{sample_data.root_id}.jpg"
                if recovered_sample_img_path.exists():
                    sample_img_path = recovered_sample_img_path
                else:
                    print(f"WARNING: {sample_img_path} does not exist, skipping sample {sample_data_path}")
                    continue

            parsed_samples.append((sample_data, sample_img_path))

    if len(parsed_samples) == 0:
        print("No conversation roots found, exiting...")
        exit(0)

    # Sort by priority (highest first)
    parsed_samples.sort(key=lambda x: x[0].priority, reverse=True)

    # Cap if max_roots is set
    if args.max_roots is not None:
        parsed_samples = parsed_samples[:args.max_roots]

    conversation_roots: list[ConversationRoot] = []

    for sample_data, sample_img_path in parsed_samples:
        # Copy the image file to the local directory
        dest_img_path = local_roots_image_dir / f"{sample_data.root_id}.jpg"
        shutil.copy(sample_img_path, dest_img_path)

        # Create the ConversationRoot entry
        root = ConversationRoot(
            root_id=f"clarif_trees_{sample_data.root_id}",
            ambiguous_question=sample_data.ambiguous_question,
            priority=sample_data.priority,
            unambiguous_question=sample_data.unambiguous_question,
            multimodal_file_path=str(dest_img_path),
            original_dataset=sample_data.original_dataset,
            original_dataset_sample_id=sample_data.original_dataset_sample_id
        )
        conversation_roots.append(root)

    print(f"Found {len(conversation_roots)} conversation roots.")

    # Save the conversation roots to a JSON file
    with open(local_roots_data_path, "w") as f:
        # ConversationRoot inherits from BaseModel
        roots_data = {"roots": [root.model_dump() for root in conversation_roots]}
        json.dump(roots_data, f, indent=4)

if __name__ == "__main__":
    main()
