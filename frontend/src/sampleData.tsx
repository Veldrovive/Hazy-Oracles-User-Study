import { type RatingQuestion } from './components/RatingForm';

// --- Sample Data ---
export const QUESTION_ANSWERER_INSTRUCTIONS = [
    "Review the Test Image and the conversation.",
    "Understand the target unambiguous question.",
    "Rate the final Clarifying Question from the Agent.",
    "Use the information to formulate your next unambiguous response."
];
export const QUESTION_ASKER_INSTRUCTIONS = [
    "Formulate the target question in an unambiguous way.",
    "Provide the image with region labels (if needed).",
    "Receive clarifying questions from the assistant.",
    "Answer the questions to the best of your ability.",
    "Ask follow-up questions if the previous answers are not sufficient to make the question unambiguous.",
    "Rate the assistant's response in terms of relevance.",
];

export const QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_TITLE = "Detailed Instructions"
export const QUESTION_ASKER_DETAILED_INSTRUCTIONS_TITLE = "Detailed Instructions"

export const QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_CONTENT = <>
    <p>Detailed instructions</p>
    <ul>
        <li>Instruction 1</li>
    </ul>
</>
export const QUESTION_ASKER_DETAILED_INSTRUCTIONS_CONTENT = <>
    <p>Detailed instructions</p>
    <ul>
        <li>Instruction 1</li>
    </ul>
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
        url: 'https://beentheredonethatwithkids.com/wp-content/uploads/2016/07/Virginia-Safari-Park-Zebra-in-Car-scaled.jpg'
    },
    ambiguous_question: 'Where is the large white item?',
    intended_question: 'What is the precise location of the zebra relative to the red car?',
    dialog_history: [
        {
            role: 'question_asker',
            text: 'Are you talking about the animal?'
        },
        {
            role: 'question_answerer',
            text: 'Yes.'
        }
    ]
};

export const DUMMY_ANSWERER_SAMPLE: SampleData = {
    sample_id: 'dummy_answerer',
    task_role: 'question_answerer',
    multimodal_input: {
        type: 'image',
        url: 'https://beentheredonethatwithkids.com/wp-content/uploads/2016/07/Virginia-Safari-Park-Zebra-in-Car-scaled.jpg'
    },
    ambiguous_question: 'Where is the large white item?',
    intended_question: 'What is the precise location of the zebra relative to the red car?',
    dialog_history: [
        {
            role: 'question_asker',
            text: 'Are you talking about the animal?'
        },
        {
            role: 'question_answerer',
            text: 'Yes.'
        },
        {
            role: 'question_asker',
            text: 'The one sticking it\'s head in the window?'
        }
    ]
};
