import { Box, Typography } from '@mui/material';

interface TargetQuestionProps {
    question: string;
    setIsHovered: (isHovered: boolean) => void;
}

export function TargetQuestion({ question, setIsHovered }: TargetQuestionProps) {
    return (
        <Box
            id="intended-question"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            sx={{
                p: 2,
                mb: 2,
                bgcolor: '#e8f5e9', // light green background
                borderRadius: 1,
                border: '1px solid #a5d6a7',
            }}
        >
            <Typography variant="h6" gutterBottom>
                Intended Question
            </Typography>
            <Typography variant="body1">{question}</Typography>
        </Box>
    );
}
