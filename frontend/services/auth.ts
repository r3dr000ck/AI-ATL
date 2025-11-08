const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/auth';

export interface User {
  id: string;
  email: string;
  name: string;
  date_joined: string;
  profile: UserProfile;
}

export interface UserProfile {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  broker_capital: string;
  max_position_size: string | null;
  email_notifications: boolean;
  trade_alerts: boolean;
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
}

export interface RegisterData {
  email: string;
  name: string;
  password: string;
  confirm_password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  message: string;
}

class AuthService {
  private getHeaders(includeAuth: boolean = false): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
    }

    return headers;
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/register/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }

    const result = await response.json();
    this.setToken(result.token);
    return result;
  }

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/login/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }

    const result = await response.json();
    this.setToken(result.token);
    return result;
  }

  async logout(): Promise<void> {
    const response = await fetch(`${API_URL}/logout/`, {
      method: 'POST',
      headers: this.getHeaders(true),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Logout failed');
    }

    this.removeToken();
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_URL}/me/`, {
      method: 'GET',
      headers: this.getHeaders(true),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    return response.json();
  }

  async getUserProfile(): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/profile/`, {
      method: 'GET',
      headers: this.getHeaders(true),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch profile');
    }

    return response.json();
  }

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/profile/`, {
      method: 'PATCH',
      headers: this.getHeaders(true),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Profile update failed');
    }

    const result = await response.json();
    return result.profile;
  }

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

export const authService = new AuthService();
