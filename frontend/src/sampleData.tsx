import { type RatingQuestion } from './components/RatingForm';

// --- Sample Data ---
export const QUESTION_ANSWERER_INSTRUCTIONS = [
    "Review the image and the conversation.",
    "Review the intended question.",
    "Rate the previous clarifying question.",
    "Respond to the clarifying question."
];
export const QUESTION_ASKER_INSTRUCTIONS = [
    "Review the image and the conversation.",
    "Rate the quality of the previous response.",
    "Attempt to answer the original question.",
    "Formulate a new clarifying question that you think will reduce the ambiguity of the situation."
];

export const QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_TITLE = "Question Asker Role Instructions"
export const QUESTION_ASKER_DETAILED_INSTRUCTIONS_TITLE = "Question Answerer Role Instructions"

export const QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_CONTENT = <>
    <p>In this study, you will repeatedly be presented with a partial conversation and be tasked with adding the next message in the dialog. "Answerer" is one of two roles you will play in this study. The "answerer" role is meant to answer a clarifying question.</p>
    <i>If the previous response is not a clarifying question, you should not answer. Instead, say something like "that is not a question."</i>
</>
export const QUESTION_ASKER_DETAILED_INSTRUCTIONS_CONTENT = <>
    <p>In this study, you will repeatedly be presented with a partial conversation and be tasked with adding the next message in the dialog. "Asker" is one of two roles you will play in this study. The "asker" role is meant to ask a clarifying question.</p>
    <i>Even if it seems to you like there is nothing to ask about, please attempt to formulate a meaningful clarifying question</i>
</>


export const QUESTION_ANSWERER_RATING_QUESTIONS: RatingQuestion[] = [
    {
        id: "relevance",
        label: "Rate relevance (1-5)",
        details: "How relevant is this clarifying question to resolving the ambiguity?",
        marks: [
            { value: 1, label: '1' },
            { value: 2, label: '2' },
            { value: 3, label: '3' },
            { value: 4, label: '4' },
            { value: 5, label: '5' },
        ],
        valueLabels: [
            { value: 1, label: 'Not at all relevant' },
            { value: 2, label: 'Not very relevant' },
            { value: 3, label: 'Neutral' },
            { value: 4, label: 'Very relevant' },
            { value: 5, label: 'Perfectly relevant' },
        ]
    }
];
export const QUESTION_ASKER_RATING_QUESTIONS: RatingQuestion[] = [
    {
        id: "helpfulness",
        label: "Rate helpfulness (1-5)",
        details: "How helpful was this response in making the question unambiguous?",
        marks: [
            { value: 1, label: '1' },
            { value: 2, label: '2' },
            { value: 3, label: '3' },
            { value: 4, label: '4' },
            { value: 5, label: '5' },
        ],
        valueLabels: [
            { value: 1, label: 'Not at all helpful' },
            { value: 2, label: 'Not very helpful' },
            { value: 3, label: 'Neutral' },
            { value: 4, label: 'Very helpful' },
            { value: 5, label: 'Perfectly helpful' },
        ]
    }
]

import type { SampleData } from './Sample';

export const DUMMY_ASKER_SAMPLE: SampleData = {
    sample_id: 'dummy_asker',
    task_role: 'question_asker',
    multimodal_input: {
        type: 'image',
        url: '/example_img.jpg'
    },
    ambiguous_question: 'Who is associated with this stuffed animal?',
    intended_question: 'Which american president is most associated with the stuffed animal seen here?',
    dialog_history: [
        {
            role: 'question_asker',
            text: 'There are many types of association. Do you mean who is this bear dressed as?'
        },
        {
            role: 'question_answerer',
            text: 'Yes, I meant who is he dressed as.'
        }
    ]
};

export const DUMMY_ANSWERER_SAMPLE: SampleData = {
    sample_id: 'dummy_answerer',
    task_role: 'question_answerer',
    multimodal_input: {
        type: 'image',
        url: '/example_img.jpg'
    },
    ambiguous_question: 'Who is associated with this stuffed animal?',
    intended_question: 'Which american president is most associated with the stuffed animal seen here?',
    dialog_history: [
        {
            role: 'question_asker',
            text: 'There are many types of association. Do you mean who is this bear dressed as?'
        },
        {
            role: 'question_answerer',
            text: 'Yes, I meant who is he dressed as.'
        },
        {
            role: 'question_asker',
            text: 'Is the wine also relevant?'
        }
    ]
};
