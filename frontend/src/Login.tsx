import { useState } from 'react';
import { Box, Typography, TextField, Button, Container, Link, Alert, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { isLoginValid } from './utils'

import { useLocalStorage } from 'usehooks-ts'

declare const __DEV_API_KEY__: string | undefined;

function Login() {
    const [currentLoginId, setCurrentLoginId] = useState('');
    const [currentPassword, setCurrentPassword] = useState('');
    const [currentError, setCurrentError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Dev create user state
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [createUsername, setCreateUsername] = useState('');
    const [createPassword, setCreatePassword] = useState('');
    const [createApiKey, setCreateApiKey] = useState(typeof __DEV_API_KEY__ !== 'undefined' ? __DEV_API_KEY__ : '');
    const [createStatus, setCreateStatus] = useState('');
    const [isCreating, setIsCreating] = useState(false);

    const handleCreateUser = async () => {
        setIsCreating(true);
        setCreateStatus('');
        try {
            const res = await fetch('/api/v1/user/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: createApiKey,
                    login_id: createUsername || undefined,
                    password: createPassword || undefined,
                })
            });
            const data = await res.json();
            if (res.ok) {
                setCreateStatus('User created successfully');
            } else {
                setCreateStatus(`Error: ${data.detail?.message || 'Unknown error'}`);
            }
        } catch (e) {
            setCreateStatus('Failed to create user');
        }
        setIsCreating(false);
    };

    const [, setSavedLoginId] = useLocalStorage('loginId', '')
    const [, setSavedPassword] = useLocalStorage('password', '')
    const [, setHasCompletedConsent] = useLocalStorage('has_consented', false)

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

            try {
                const summaryRes = await fetch('/api/v1/user/summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ login_id: currentLoginId, password: currentPassword })
                });
                if (summaryRes.ok) {
                    const summaryData = await summaryRes.json();
                    if (summaryData.data.has_consented) {
                        setHasCompletedConsent(true);
                        navigate('/sample');
                    } else {
                        setHasCompletedConsent(false);
                        navigate('/consent');
                    }
                } else {
                    setCurrentError('Failed to fetch user summary');
                }
            } catch (e) {
                setCurrentError('Failed to fetch user summary');
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
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        {import.meta.env.DEV ? (
                            <Button
                                variant="text"
                                onClick={() => setCreateModalOpen(true)}
                                sx={{ textTransform: 'none', color: 'text.secondary' }}
                            >
                                Dev: Create User
                            </Button>
                        ) : (
                            <Box />
                        )}
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

            <Typography variant="body1" color="text.secondary" align="center" sx={{ mt: 'auto' }}>
                For questions contact: <Link href="mailto:adempst@umich.edu" color="inherit">adempst@umich.edu</Link>
            </Typography>

            {import.meta.env.DEV && (
                <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)}>
                    <DialogTitle>Create Dev User</DialogTitle>
                    <DialogContent>
                        {createStatus && (
                            <Alert severity={createStatus.startsWith('Error') || createStatus.startsWith('Failed') ? 'error' : 'success'} sx={{ mb: 2, mt: 1 }}>
                                {createStatus}
                            </Alert>
                        )}
                        <TextField
                            label="Username (Login ID)"
                            variant="outlined"
                            value={createUsername}
                            onChange={(e) => setCreateUsername(e.target.value)}
                            fullWidth
                            margin="normal"
                            disabled={isCreating}
                        />
                        <TextField
                            label="Password"
                            variant="outlined"
                            value={createPassword}
                            onChange={(e) => setCreatePassword(e.target.value)}
                            fullWidth
                            margin="normal"
                            disabled={isCreating}
                        />
                        <TextField
                            label="API Key"
                            variant="outlined"
                            value={createApiKey}
                            onChange={(e) => setCreateApiKey(e.target.value)}
                            fullWidth
                            margin="normal"
                            type="password"
                            disabled={isCreating}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setCreateModalOpen(false)} disabled={isCreating}>Cancel</Button>
                        <Button onClick={handleCreateUser} disabled={isCreating} variant="contained" disableElevation sx={{ bgcolor: '#e6dbf9', color: '#000', '&:hover': { bgcolor: '#d5c4f5' } }}>
                            {isCreating ? <CircularProgress size={24} color="inherit" /> : 'Create'}
                        </Button>
                    </DialogActions>
                </Dialog>
            )}
        </Container>
    );
}

export default Login;