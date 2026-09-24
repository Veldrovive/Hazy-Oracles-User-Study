import { useEffect, useMemo, useRef, useState } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import { useSessionCheck } from './utils';
import { TaskInstructions } from './components/TaskInstructions';
import { TargetQuestion } from './components/TargetQuestion';
import { RatingForm } from './components/RatingForm';
import { AgentChat } from './components/AgentChat';
import Xarrow, { useXarrow } from "react-xarrows";
import {
    QUESTION_ANSWERER_INSTRUCTIONS,
    QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_TITLE,
    QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_CONTENT,
    QUESTION_ASKER_INSTRUCTIONS,
    QUESTION_ASKER_DETAILED_INSTRUCTIONS_TITLE,
    QUESTION_ASKER_DETAILED_INSTRUCTIONS_CONTENT,
    EXAMPLE_IMAGE_URL,
    EXAMPLE_TARGET_QUESTION,
    QUESTION_ANSWERER_RATING_QUESTIONS,
    QUESTION_ASKER_RATING_QUESTIONS,
    EXAMPLE_CHAT_MESSAGES
} from './sampleData';
import { useBoolean } from 'usehooks-ts';

// -------------------

export interface MultimodalInput {
    type: 'image' | 'text',
    content: string  // Could be text or a url
}

export interface DialogMessage {
    role: 'question_asker' | 'question_answerer',
    text: string
}

export interface SampleData {
    sample_id: string,
    task_role: 'question_asker' | 'question_answerer',
    multimodal_input: MultimodalInput,
    ambiguous_question: string,
    intended_question: string,
    dialog_history: DialogMessage[]
}

export interface SampleDataResponse {
    status: 'success' | 'no_sample' | 'error',
    data: SampleData
}

function SampleWrapper() {
    const isValidated = useSessionCheck();
    const testSample: SampleData = {
        sample_id: "test",
        task_role: "question_answerer",
        multimodal_input: {
            type: "image",
            content: EXAMPLE_IMAGE_URL
        },
        ambiguous_question: "Where is the large white item?",
        intended_question: EXAMPLE_TARGET_QUESTION,
        dialog_history: [
            {
                role: "question_asker",
                text: "Which specific white item are you looking for?"
            },
            {
                role: "question_answerer",
                text: "The large one next to the car."
            },
            {
                role: "question_asker",
                text: "Are you referring to the zebra?"
            }
        ]
    }

    if (!isValidated) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Sample {...testSample} isValidated={isValidated} />
    )
}

function Sample({ sample_id, task_role, multimodal_input, ambiguous_question, intended_question, dialog_history, isValidated }: SampleData & { isValidated: boolean }) {
    const [ratings, setRatings] = useState<Record<string, number>>({});

    const [currentErrorAlert, setCurrentErrorAlert] = useState<string | undefined>();

    const { value: isSendingResponse, setTrue: setIsSendingResponseTrue, setFalse: setIsSendingResponseFalse } = useBoolean(false)

    const ratingBoxRef = useRef(null);
    const lastResponseRef = useRef(null);
    const firstResponseRef = useRef(null);

    const [isIntendedQuestionhovered, setIsIntendedQuestionHovered] = useState(false);
    const [showXarrow, setShowXarrow] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowXarrow(true);
        }, 100);
        return () => clearTimeout(timer);
    }, []);

    const { instructions, detailed_instructions_title, detailed_instructions_content, rating_questions } = useMemo(() => {
        switch (task_role) {
            case 'question_answerer':
                return {
                    instructions: QUESTION_ANSWERER_INSTRUCTIONS,
                    detailed_instructions_title: QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_TITLE,
                    detailed_instructions_content: QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_CONTENT,
                    rating_questions: QUESTION_ANSWERER_RATING_QUESTIONS,
                };
            case 'question_asker':
                return {
                    instructions: QUESTION_ASKER_INSTRUCTIONS,
                    detailed_instructions_title: QUESTION_ASKER_DETAILED_INSTRUCTIONS_TITLE,
                    detailed_instructions_content: QUESTION_ASKER_DETAILED_INSTRUCTIONS_CONTENT,
                    rating_questions: QUESTION_ASKER_RATING_QUESTIONS,
                };
            default:
                throw new Error(`Unknown task role: ${task_role}`);
        }
    }, [task_role])

    const chatHistory = useMemo(() => {
        const history = dialog_history.map((message, idx) => {
            const sender = message.role
            const direction = sender === task_role ? 'outgoing' : 'incoming'
            const senderLabel = sender === 'question_asker' ? 'You' : 'Other'
            return {
                id: `msg-${idx + 1}`,
                message: message.text,
                sender: senderLabel,
                direction: direction,
                position: 'single'
            }
        })

        history.unshift({
            id: `msg-${0}`,
            message: ambiguous_question,
            sender: 'You',
            direction: task_role === 'question_asker' ? 'incoming' : 'outgoing',
            position: 'single'
        })
        return history
    }, [dialog_history, task_role])

    const handleRatingChange = (id: string, value: number) => {
        setRatings(prev => ({ ...prev, [id]: value }));
    };

    const handleSend = async (res: string) => {
        if (!isValidated) {
            setCurrentErrorAlert('Login not validated. Please wait a moment and retry.');
            return;
        }
        setIsSendingResponseTrue();
        console.log("Sending response:", res);
        await new Promise(resolve => setTimeout(resolve, 2000));
        setIsSendingResponseFalse();
        console.log("Sent response")
    }

    return (
        <>
            {showXarrow && (
                <Xarrow
                    start='rating-box'
                    startAnchor={'auto'}
                    end={lastResponseRef}
                    endAnchor={'auto'}
                    zIndex={100}
                    curveness={0.4}
                />
            )}
            {
                isIntendedQuestionhovered &&
                <Xarrow
                    end="intended-question"
                    endAnchor="auto"
                    labels={{ end: "Intended to ask" }}
                    start={firstResponseRef}
                    startAnchor="auto"
                    zIndex={100}
                    color="red"
                    curveness={0.4}
                />
            }
            <Box sx={{
                width: '100vw',
                height: '100vh',
                padding: '24px',
                boxSizing: 'border-box',
                display: 'flex',
                flexDirection: 'row',
                gap: '24px',
                backgroundColor: '#f5f5f5' // Light grey background
            }}>
                <Box sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    flex: 1, // Take up remaining space, proportional
                    maxWidth: '500px',
                    justifyContent: "space-between"
                }}>
                    <TaskInstructions instructions={instructions} modalTitle={detailed_instructions_title} modalContent={detailed_instructions_content} />
                    <Box sx={{
                        display: "flex",
                        flexDirection: "column"
                    }}>
                        {
                            task_role === 'question_answerer'
                                ? <TargetQuestion question={intended_question} setIsHovered={setIsIntendedQuestionHovered} />
                                : null
                        }

                        <RatingForm
                            title="Rate the previous clarifying question"
                            questions={rating_questions}
                            values={ratings}
                            onChange={handleRatingChange}
                            boxRef={ratingBoxRef}
                        />
                    </Box>
                </Box>
                <Box sx={{
                    display: 'flex',
                    flex: 2, // Take up twice the space
                    flexDirection: "column",
                    backgroundColor: 'white',
                    borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    overflow: 'hidden' // For rounded corners
                }}>
                    <AgentChat
                        imageSrc={multimodal_input.type === 'image' ? multimodal_input.content : ''}
                        imageSide={task_role === 'question_asker' ? 'incoming' : 'outgoing'}
                        initialMessages={chatHistory}
                        onSend={handleSend}
                        lastResponseRef={lastResponseRef}
                        firstResponseRef={firstResponseRef}
                        loading={!isValidated || isSendingResponse}
                    />
                    {
                        currentErrorAlert && (
                            <Alert severity="error">{currentErrorAlert}</Alert>
                        )
                    }
                </Box>
            </Box>
        </>
    );
}

export default SampleWrapper;