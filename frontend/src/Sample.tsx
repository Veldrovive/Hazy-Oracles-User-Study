import { useEffect, useMemo, useRef, useState } from 'react';
import { Box, CircularProgress, Alert, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Tooltip, IconButton, ToggleButton, ToggleButtonGroup } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import SentimentVeryDissatisfiedIcon from '@mui/icons-material/SentimentVeryDissatisfied';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import SentimentNeutralIcon from '@mui/icons-material/SentimentNeutral';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import SentimentVerySatisfiedIcon from '@mui/icons-material/SentimentVerySatisfied';
import { TaskInstructions } from './components/TaskInstructions';
import { TargetQuestion } from './components/TargetQuestion';
import { RatingForm } from './components/RatingForm';
import { AgentChat } from './components/AgentChat';
import Xarrow from "react-xarrows";
import {
    QUESTION_ANSWERER_INSTRUCTIONS,
    QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_TITLE,
    QUESTION_ANSWERER_DETAILED_INSTRUCTIONS_CONTENT,
    QUESTION_ASKER_INSTRUCTIONS,
    QUESTION_ASKER_DETAILED_INSTRUCTIONS_TITLE,
    QUESTION_ASKER_DETAILED_INSTRUCTIONS_CONTENT,
    QUESTION_ANSWERER_RATING_QUESTIONS,
    QUESTION_ASKER_RATING_QUESTIONS
} from './sampleData';
import { useBoolean, useLocalStorage } from 'usehooks-ts';
import { useNavigate } from 'react-router-dom';

// -------------------

export interface MultimodalInput {
    type: 'image' | 'text',
    url: string
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
    const [loginId, setLoginId] = useLocalStorage('loginId', '');
    const [password, setPassword] = useLocalStorage('password', '');
    const [, setHasConsented] = useLocalStorage('has_consented', false);
    const navigate = useNavigate();

    const [sampleData, setSampleData] = useState<SampleData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [noSampleReason, setNoSampleReason] = useState<string | null>(null);

    const [hasReadAsker, setHasReadAsker] = useState(true);
    const [hasReadAnswerer, setHasReadAnswerer] = useState(true);

    useEffect(() => {
        let isMounted = true;
        const load = async () => {
            if (!loginId || !password) {
                navigate('/?message=' + encodeURIComponent('Please enter your login id and password again'));
                return;
            }

            try {
                const summaryRes = await fetch('/api/v1/user/summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ login_id: loginId, password })
                });

                if (!summaryRes.ok) {
                    setLoginId('');
                    setPassword('');
                    setHasConsented(false);
                    navigate('/?message=' + encodeURIComponent('Please enter your login id and password again'));
                    return;
                }

                const summaryData = await summaryRes.json();
                if (!summaryData.data.has_consented) {
                    navigate('/consent');
                    return;
                }

                if (!isMounted) return;
                setHasReadAsker(summaryData.data.has_read_asker_instructions);
                setHasReadAnswerer(summaryData.data.has_read_answerer_instructions);

                const sampleRes = await fetch('/api/v1/task/sample', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ login_id: loginId, password })
                });

                const sampleResData = await sampleRes.json();

                if (!isMounted) return;

                if (sampleResData.status === 'no_sample') {
                    setNoSampleReason(sampleResData.message || 'No samples available at this time.');
                    setIsLoading(false);
                    return;
                }

                if (sampleResData.status === 'success') {
                    setSampleData(sampleResData.data);
                    setIsLoading(false);
                }
            } catch (e) {
                console.error(e);
            }
        };

        load();
        return () => { isMounted = false; };
    }, [loginId, password, navigate, setLoginId, setPassword, setHasConsented]);

    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (noSampleReason) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
                <Typography variant="h5" gutterBottom>No sample</Typography>
                <Typography>{noSampleReason}</Typography>
            </Box>
        )
    }

    if (!sampleData) return null;

    const handleLogout = () => {
        setLoginId('');
        setPassword('');
        setHasConsented(false);
        navigate('/');
    };

    return (
        <Sample
            {...sampleData}
            isValidated={true}
            hasReadAsker={hasReadAsker}
            hasReadAnswerer={hasReadAnswerer}
            loginId={loginId}
            password={password}
            setHasReadAsker={setHasReadAsker}
            setHasReadAnswerer={setHasReadAnswerer}
            handleLogout={handleLogout}
        />
    )
}

type SampleProps = SampleData & {
    isValidated: boolean,
    hasReadAsker: boolean,
    hasReadAnswerer: boolean,
    loginId: string,
    password: string,
    setHasReadAsker: (val: boolean) => void,
    setHasReadAnswerer: (val: boolean) => void,
    handleLogout: () => void
};

function Sample({ sample_id, task_role, multimodal_input, ambiguous_question, intended_question, dialog_history, isValidated, hasReadAsker, hasReadAnswerer, loginId, password, setHasReadAsker, setHasReadAnswerer, handleLogout }: SampleProps) {
    const [ratings, setRatings] = useState<Record<string, number>>({});
    const [currentGuess, setCurrentGuess] = useState("");
    const [confidenceScore, setConfidenceScore] = useState<number | null>(null);

    const [currentErrorAlert, setCurrentErrorAlert] = useState<string | undefined>();

    const { value: isSendingResponse, setTrue: setIsSendingResponseTrue, setFalse: setIsSendingResponseFalse } = useBoolean(false)

    const ratingBoxRef = useRef<any>(null);
    const lastResponseRef = useRef<any>(null);
    const firstResponseRef = useRef<any>(null);

    const [isIntendedQuestionhovered, setIsIntendedQuestionHovered] = useState(false);
    const [isCurrentGuessHovered, setIsCurrentGuessHovered] = useState(false);
    const [isCurrentGuessFocused, setIsCurrentGuessFocused] = useState(false);
    const [showXarrow, setShowXarrow] = useState(false);

    const [showInstructionsModal, setShowInstructionsModal] = useState(
        (task_role === 'question_asker' && !hasReadAsker) ||
        (task_role === 'question_answerer' && !hasReadAnswerer)
    );

    const handleReadInstructions = async () => {
        const endpoint = task_role === 'question_asker' ? '/api/v1/user/read_asker_instructions' : '/api/v1/user/read_answerer_instructions';
        try {
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ login_id: loginId, password })
            });
            if (task_role === 'question_asker') {
                setHasReadAsker(true);
            } else {
                setHasReadAnswerer(true);
            }
        } catch (e) {
            console.error(e);
        }
        setShowInstructionsModal(false);
    };

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

    const handleSend = async (res: string): Promise<boolean> => {
        if (!isValidated) {
            setCurrentErrorAlert('Login not validated. Please wait a moment and retry.');
            return false;
        }

        if (dialog_history.length > 0) {
            if (task_role === 'question_answerer') {
                if (!ratings['relevance']) {
                    setCurrentErrorAlert('Please fill out all ratings before sending.');
                    return false;
                }
            } else if (task_role === 'question_asker') {
                if (!ratings['helpfulness']) {
                    setCurrentErrorAlert('Please fill out the helpfulness rating before sending.');
                    return false;
                }
            }
        }

        if (task_role === 'question_asker') {
            if (!currentGuess.trim()) {
                setCurrentErrorAlert('Please enter your current guess.');
                return false;
            }
            if (confidenceScore === null) {
                setCurrentErrorAlert('Please select a confidence score.');
                return false;
            }
        }

        setCurrentErrorAlert(undefined);
        setIsSendingResponseTrue();
        console.log("Sending response:", res);

        let response_data: any = {};
        if (task_role === 'question_asker') {
            response_data = {
                response_type: 'question_asker',
                previous_answer_meaningful_score: ratings['helpfulness'],
                current_guess: currentGuess,
                confidence_score: confidenceScore,
                next_question: res
            };
        } else {
            response_data = {
                response_type: 'question_answerer',
                previous_question_relevant_score: ratings['relevance'],
                answer: res
            };
        }

        try {
            const apiRes = await fetch('/api/v1/task/response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    login_id: loginId,
                    password: password,
                    sample_id: sample_id,
                    response_data: response_data
                })
            });

            if (!apiRes.ok) {
                const errData = await apiRes.json();
                setCurrentErrorAlert(errData.detail?.message || 'Error submitting response.');
                setIsSendingResponseFalse();
                return false;
            }

            console.log("Sent response successfully");
            window.location.reload();
            return true;
        } catch (e: any) {
            console.error(e);
            setCurrentErrorAlert(e.message || 'An unexpected error occurred.');
            setIsSendingResponseFalse();
            return false;
        }
    }

    return (
        <>
            <Dialog open={showInstructionsModal} onClose={() => { }} maxWidth="md" fullWidth>
                <DialogTitle>{detailed_instructions_title}</DialogTitle>
                <DialogContent>
                    <Box sx={{ whiteSpace: 'pre-wrap', pt: 1 }}>{detailed_instructions_content}</Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleReadInstructions} variant="contained" color="primary">
                        I have read the instructions
                    </Button>
                </DialogActions>
            </Dialog>

            {showXarrow && dialog_history.length > 0 && (
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
            {
                (isCurrentGuessHovered || isCurrentGuessFocused) &&
                <Xarrow
                    end={firstResponseRef}
                    endAnchor="auto"
                    start="current-guess-box"
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

                        {dialog_history.length > 0 && (
                            <RatingForm
                                title={task_role === 'question_asker' ? "Rate the previous answer" : "Rate the previous clarifying question"}
                                questions={rating_questions}
                                values={ratings}
                                onChange={handleRatingChange}
                                boxRef={ratingBoxRef}
                            />
                        )}

                        {
                            task_role === 'question_asker' && (
                                <Box sx={{ mt: 2, p: 2, bgcolor: 'white', borderRadius: 1, border: '1px solid #e0e0e0', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                                    <Typography variant="h6" gutterBottom>
                                        Answer the original question
                                    </Typography>
                                    <TextField
                                        id="current-guess-box"
                                        fullWidth
                                        size="small"
                                        label="What is your best guess for the answer to this original question?"
                                        value={currentGuess}
                                        onChange={(e) => setCurrentGuess(e.target.value)}
                                        onMouseEnter={() => setIsCurrentGuessHovered(true)}
                                        onMouseLeave={() => setIsCurrentGuessHovered(false)}
                                        onFocus={() => setIsCurrentGuessFocused(true)}
                                        onBlur={() => setIsCurrentGuessFocused(false)}
                                        sx={{ mb: 2 }}
                                    />
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="body1">
                                            Confidence Score (1-5)
                                        </Typography>
                                        <Tooltip title="How confident are you that you are correct?" placement="right">
                                            <IconButton size="small" sx={{ ml: 1, color: 'action.active' }}>
                                                <InfoIcon fontSize="small" />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                    <Box sx={{ width: '100%' }}>
                                        <ToggleButtonGroup
                                            value={confidenceScore}
                                            exclusive
                                            fullWidth
                                            onChange={(_, newValue) => {
                                                if (newValue !== null) {
                                                    setConfidenceScore(newValue);
                                                }
                                            }}
                                            aria-label="confidence score"
                                        >
                                            <Tooltip title="Not at all confident" placement="top">
                                                <ToggleButton value={1} aria-label="not at all confident">
                                                    <SentimentVeryDissatisfiedIcon />
                                                </ToggleButton>
                                            </Tooltip>
                                            <Tooltip title="Not very confident" placement="top">
                                                <ToggleButton value={2} aria-label="not very confident">
                                                    <SentimentDissatisfiedIcon />
                                                </ToggleButton>
                                            </Tooltip>
                                            <Tooltip title="Neutral" placement="top">
                                                <ToggleButton value={3} aria-label="neutral">
                                                    <SentimentNeutralIcon />
                                                </ToggleButton>
                                            </Tooltip>
                                            <Tooltip title="Very confident" placement="top">
                                                <ToggleButton value={4} aria-label="very confident">
                                                    <SentimentSatisfiedIcon />
                                                </ToggleButton>
                                            </Tooltip>
                                            <Tooltip title="Perfectly confident" placement="top">
                                                <ToggleButton value={5} aria-label="perfectly confident">
                                                    <SentimentVerySatisfiedIcon />
                                                </ToggleButton>
                                            </Tooltip>
                                        </ToggleButtonGroup>
                                    </Box>
                                </Box>
                            )
                        }
                        <Button
                            variant="outlined"
                            color="error"
                            onClick={handleLogout}
                            sx={{ mt: 2 }}
                        >
                            Log Out
                        </Button>
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
                        imageSrc={multimodal_input.type === 'image' ? multimodal_input.url : ''}
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