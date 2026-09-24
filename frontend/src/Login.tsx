import { useState } from 'react';
import { Box, Typography, TextField, Button, Container, Link, Alert, CircularProgress } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { isLoginValid } from './utils'

import { useLocalStorage } from 'usehooks-ts'

function Login() {
    const [currentLoginId, setCurrentLoginId] = useState('');
    const [currentPassword, setCurrentPassword] = useState('');
    const [currentError, setCurrentError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const [savedLoginId, setSavedLoginId] = useLocalStorage('loginId', '')
    const [savedPassword, setSavedPassword] = useLocalStorage('password', '')
    const [hasCompletedConsent, setHasCompletedConsent] = useLocalStorage('has_consented', false)

    const navigate = useNavigate();
    const location = useLocation();
    const urlMessage = new URLSearchParams(location.search).get('message');

    const handleLogin = async () => {
        setIsLoading(true);
        const isValid = await isLoginValid(currentLoginId, currentPassword);
        setIsLoading(false);

        if (isValid) {
            setCurrentError('');
            setSavedLoginId(currentLoginId)
            setSavedPassword(currentPassword)

            if (hasCompletedConsent) {
                navigate('/sample');
            } else {
                navigate('/consent');
            }
        } else {
            setCurrentError('Invalid login credentials');
        }
    };

    return (
        <Container
            maxWidth="md"
            sx={{
                display: 'flex',
                flexDirection: 'column',
                minHeight: '100vh',
                justifyContent: 'center',
                py: 4
            }}
        >
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <Typography
                    variant="h4"
                    component="h1"
                    gutterBottom
                    sx={{ mb: 3, textAlign: 'center' }}
                >
                    Understanding How Humans Ask and Answer Clarifying Questions
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 8, fontWeight: 400 }}>
                    IRB: HUM00299042
                </Typography>

                <Box sx={{ width: '100%', maxWidth: 400, display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {urlMessage && !currentError && (
                        <Alert severity="info">
                            {urlMessage}
                        </Alert>
                    )}
                    {currentError && (
                        <Alert severity="error">
                            {currentError}
                        </Alert>
                    )}
                    <TextField
                        label="Login Id"
                        variant="outlined"
                        value={currentLoginId}
                        onChange={(e) => setCurrentLoginId(e.target.value)}
                        fullWidth
                        disabled={isLoading}
                    />
                    <TextField
                        label="Password"
                        type="password"
                        variant="outlined"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        fullWidth
                        disabled={isLoading}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                            variant="contained"
                            onClick={handleLogin}
                            disabled={isLoading}
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
                            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Log In'}
                        </Button>
                    </Box>
                </Box>
            </Box>

            <Typography variant="body1" color="text.secondary" align="center" mt="auto">
                For questions contact: <Link href="mailto:adempst@umich.edu" color="inherit">adempst@umich.edu</Link>
            </Typography>
        </Container>
    );
}

export default Login;