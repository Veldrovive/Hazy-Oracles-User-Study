import { Box, Typography, Slider, Tooltip, IconButton } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

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
                    <Box sx={{ px: 2 }}>
                        <Slider
                            value={values[q.id] || 3}
                            min={q.min || 1}
                            max={q.max || 5}
                            step={1}
                            marks={q.marks || false}
                            onChange={(_, newValue) => onChange(q.id, newValue as number)}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(value) => valueLabelFormat(q, value)}
                        />
                    </Box>
                </Box>
            ))}
        </Box>
    );
}
