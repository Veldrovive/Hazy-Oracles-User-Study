import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocalStorage } from 'usehooks-ts';
import isLoginValid from './isLoginValid';

function useSessionCheck() {
    const [loginId, setLoginId] = useLocalStorage('loginId', '');
    const [password, setPassword] = useLocalStorage('password', '');
    const [, setHasConsented] = useLocalStorage('has_consented', false);
    const navigate = useNavigate();
    const [isValidated, setIsValidated] = useState(false);

    useEffect(() => {
        let isMounted = true;
        const check = async () => {
            const valid = await isLoginValid(loginId, password);
            if (!isMounted) return;

            if (!valid) {
                setLoginId('');
                setPassword('');
                setHasConsented(false);
                navigate('/?message=' + encodeURIComponent('Please enter your login id and password again'));
            } else {
                setIsValidated(true);
            }
        };

        check();
        const interval = setInterval(check, 60000); // Check every minute
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [loginId, password, navigate, setLoginId, setPassword, setHasConsented]);

    return isValidated;
}

export default useSessionCheck;
