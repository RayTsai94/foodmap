// Token 儲存的 key
const TOKEN_KEY = 'auth_token';

// 儲存 token
export const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

// 獲取 token
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

// 移除 token
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

// 檢查是否已登入
export const isAuthenticated = () => {
  return !!getToken();
}; 