import { useState } from 'react';
import { Box, Typography, TextField, Button, Checkbox, FormControlLabel, Container, IconButton, CircularProgress } from '@mui/material';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import { useNavigate } from 'react-router-dom';
import { useLocalStorage } from 'usehooks-ts';
import { Document, Page, pdfjs } from 'react-pdf';
import { useSessionCheck } from './utils';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

function Consent() {
    const isValidated = useSessionCheck();
    const [, setHasConsented] = useLocalStorage('has_consented', false);
    const [isCheckboxChecked, setIsCheckboxChecked] = useState(false);
    const [fullName, setFullName] = useState('');
    const navigate = useNavigate();

    const [numPages, setNumPages] = useState<number>();
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [hasReachedLastPage, setHasReachedLastPage] = useState(false);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }): void {
        setNumPages(numPages);
        if (numPages === 1) {
            setHasReachedLastPage(true);
        }
    }

    const goToPrevPage = () => {
        setPageNumber((prev) => Math.max(prev - 1, 1));
    };

    const goToNextPage = () => {
        setPageNumber((prev) => {
            const next = Math.min(prev + 1, numPages || 1);
            if (next === numPages) {
                setHasReachedLastPage(true);
            }
            return next;
        });
    };

    const handleSubmit = () => {
        if (isCheckboxChecked && fullName.trim() !== '') {
            setHasConsented(true);
            navigate('/sample');
        }
    };

    if (!isValidated) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Container maxWidth="md" sx={{ py: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Box sx={{ mb: 2, width: '100%', display: 'flex', justifyContent: 'center', overflow: 'hidden' }}>
                <Document file="/consent.pdf" onLoadSuccess={onDocumentLoadSuccess}>
                    <Page pageNumber={pageNumber} width={800} />
                </Document>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mb: 4 }}>
                <IconButton onClick={goToPrevPage} disabled={pageNumber <= 1}>
                    <ArrowBackIosNewIcon fontSize="small" />
                </IconButton>
                <Typography>
                    Page {pageNumber} of {numPages || '--'}
                </Typography>
                <IconButton onClick={goToNextPage} disabled={pageNumber >= (numPages || 1)}>
                    <ArrowForwardIosIcon fontSize="small" />
                </IconButton>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, width: '100%', maxWidth: 400 }}>
                <FormControlLabel
                    disabled={!hasReachedLastPage}
                    control={
                        <Checkbox
                            checked={isCheckboxChecked}
                            onChange={(e) => setIsCheckboxChecked(e.target.checked)}
                            color="primary"
                            sx={{
                                color: '#ccc',
                                '&.Mui-checked': {
                                    color: '#1976d2',
                                },
                            }}
                        />
                    }
                    label={<Typography variant="h5" sx={{ fontWeight: 400 }}>I consent to be part of this research.</Typography>}
                />

                <TextField
                    disabled={!hasReachedLastPage}
                    label="Full Name"
                    variant="outlined"
                    fullWidth
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                />

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
                    <Button
                        variant="contained"
                        onClick={handleSubmit}
                        disabled={!hasReachedLastPage || !isCheckboxChecked || fullName.trim() === ''}
                        disableElevation
                        sx={{
                            bgcolor: '#e6dbf9',
                            color: '#000',
                            textTransform: 'none',
                            fontWeight: 600,
                            px: 4,
                            py: 1,
                            minWidth: 100,
                            height: 40,
                            '&:hover': {
                                bgcolor: '#d5c4f5',
                            },
                            '&.Mui-disabled': {
                                bgcolor: '#e6dbf9',
                                opacity: 0.7,
                                color: '#000',
                            }
                        }}
                    >
                        Submit
                    </Button>
                </Box>
            </Box>
        </Container>
    );
}

export default Consent;
