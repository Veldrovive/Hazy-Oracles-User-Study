import { Box, Typography, Tooltip, IconButton, ToggleButton, ToggleButtonGroup } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import SentimentVeryDissatisfiedIcon from '@mui/icons-material/SentimentVeryDissatisfied';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import SentimentNeutralIcon from '@mui/icons-material/SentimentNeutral';
import SentimentSatisfiedIcon from '@mui/icons-material/SentimentSatisfied';
import SentimentVerySatisfiedIcon from '@mui/icons-material/SentimentVerySatisfied';

export interface RatingQuestion {
    id: string;
    label: string;
    details: string;
    min?: number;
    max?: number;
    marks?: Array<{ value: number; label: string }>;
    valueLabels?: Array<{ value: number; label: string }>;
}

interface RatingFormProps {
    title: string;
    questions: RatingQuestion[];
    values: Record<string, number>;
    onChange: (id: string, value: number) => void;
    boxRef: React.RefObject<HTMLDivElement>;
}

export function RatingForm({ title, questions, values, onChange, boxRef }: RatingFormProps) {

    const valueLabelFormat = (q: RatingQuestion, value: number) => {
        if (q.valueLabels) {
            const label = q.valueLabels.find(l => l.value === value);
            if (label) {
                return label.label;
            }
        }
        return value.toString();
    }

    return (
        <Box
            ref={boxRef}
            id="rating-box"
            sx={{
                p: 2,
                bgcolor: 'white',
                borderRadius: 1,
                border: '1px solid #e0e0e0',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
        >
            <Typography variant="h6" gutterBottom>
                {title}
            </Typography>

            {questions.map((q) => (
                <Box key={q.id} sx={{ mt: 3, mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body1">
                            {q.label}
                        </Typography>
                        <Tooltip title={q.details} placement="right">
                            <IconButton size="small" sx={{ ml: 1, color: 'action.active' }}>
                                <InfoIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </Box>
                    <Box sx={{ width: '100%' }}>
                        <ToggleButtonGroup
                            value={values[q.id] || null}
                            exclusive
                            fullWidth
                            onChange={(_, newValue) => {
                                if (newValue !== null) {
                                    onChange(q.id, newValue as number);
                                }
                            }}
                            aria-label={q.label}
                        >
                            <Tooltip title={valueLabelFormat(q, 1)} placement="top">
                                <ToggleButton value={1} aria-label={valueLabelFormat(q, 1)}>
                                    <SentimentVeryDissatisfiedIcon />
                                </ToggleButton>
                            </Tooltip>
                            <Tooltip title={valueLabelFormat(q, 2)} placement="top">
                                <ToggleButton value={2} aria-label={valueLabelFormat(q, 2)}>
                                    <SentimentDissatisfiedIcon />
                                </ToggleButton>
                            </Tooltip>
                            <Tooltip title={valueLabelFormat(q, 3)} placement="top">
                                <ToggleButton value={3} aria-label={valueLabelFormat(q, 3)}>
                                    <SentimentNeutralIcon />
                                </ToggleButton>
                            </Tooltip>
                            <Tooltip title={valueLabelFormat(q, 4)} placement="top">
                                <ToggleButton value={4} aria-label={valueLabelFormat(q, 4)}>
                                    <SentimentSatisfiedIcon />
                                </ToggleButton>
                            </Tooltip>
                            <Tooltip title={valueLabelFormat(q, 5)} placement="top">
                                <ToggleButton value={5} aria-label={valueLabelFormat(q, 5)}>
                                    <SentimentVerySatisfiedIcon />
                                </ToggleButton>
                            </Tooltip>
                        </ToggleButtonGroup>
                    </Box>
                </Box>
            ))}
        </Box>
    );
}
