function isLoginValid(username: string, password: string): Promise<boolean> {
    return fetch(`/api/v1/user/login?login_id=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`)
        .then(res => res.ok)
        .catch(() => false);
}

export default isLoginValid;