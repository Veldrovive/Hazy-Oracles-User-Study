function isLoginValid(username: string, password: string): Promise<boolean> {
    // Dummy web request function
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(username === 'aidan'); // Always assume valid for now
        }, 500);
    });
}

export default isLoginValid;