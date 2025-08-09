import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { supabaseApi } from '../services/supabaseApi';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, fullName: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    console.log('🔄 AuthProvider: Starting initialization...');

    const initializeAuth = async () => {
      try {
        console.log('🔍 AuthProvider: Checking Supabase configuration...');
        
        // Check if Supabase is configured
        if (!isSupabaseConfigured()) {
          console.log('⚠️ AuthProvider: Supabase not configured, using demo mode');
          if (mounted) {
            setUser({
              id: 'demo-user',
              email: 'demo@shetkari.com',
              name: 'Demo User',
              phone: '+1-555-0123',
              farmName: 'Demo Farm',
              location: 'Demo Location',
            });
            setIsLoading(false);
            console.log('✅ AuthProvider: Demo user set, loading complete');
          }
          return;
        }

        console.log('🔍 AuthProvider: Getting initial session...');
        
        // Get session without timeout - let it take as long as needed
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('❌ AuthProvider: Error getting session:', error);
          if (mounted) {
            setIsLoading(false);
          }
          return;
        }
        
        console.log('📋 AuthProvider: Session data:', session?.user?.id ? 'User found' : 'No user');
        
        if (session?.user && mounted) {
          console.log('👤 AuthProvider: Getting user profile with session data...');
          try {
            // Pass user data from session to avoid additional auth calls
            const currentUser = await supabaseApi.getCurrentUser(
              session.user.id,
              session.user.email!,
              session.user.user_metadata
            );
            
            if (mounted) {
              console.log('✅ AuthProvider: User profile loaded:', currentUser?.name);
              setUser(currentUser);
            }
          } catch (error) {
            console.error('⚠️ AuthProvider: Error getting user profile, using fallback:', error);
            // If profile doesn't exist, user is still authenticated but needs profile setup
            if (mounted) {
              const fallbackUser = {
                id: session.user.id,
                email: session.user.email!,
                name: session.user.user_metadata?.full_name || 'User',
                phone: '',
                farmName: '',
                location: '',
              };
              console.log('✅ AuthProvider: Fallback user set:', fallbackUser.name);
              setUser(fallbackUser);
            }
          }
        } else {
          console.log('❌ AuthProvider: No session found');
        }
        
        // Always set loading to false after processing session
        if (mounted) {
          console.log('✅ AuthProvider: Setting loading to false after session check');
          setIsLoading(false);
        }
      } catch (error) {
        console.error('❌ AuthProvider: Error in initializeAuth:', error);
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    initializeAuth();

    // Only set up auth listener if Supabase is configured
    let subscription: any = null;
    
    if (isSupabaseConfigured()) {
      console.log('🔗 AuthProvider: Setting up auth state listener...');
      // Listen for auth changes
      const { data: { subscription: authSubscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          console.log('🔄 AuthProvider: Auth state changed:', event, session?.user?.id || 'no user');
          
          if (!mounted) {
            console.log('⚠️ AuthProvider: Component unmounted, ignoring auth change');
            return;
          }
          
          if (event === 'SIGNED_IN' && session?.user) {
            console.log('✅ AuthProvider: User signed in, getting profile with session data...');
            setIsLoading(true); // Set loading while fetching profile
            
            try {
              // Pass user data from session to avoid additional auth calls
              
              const fallbackUser = {
                id: session.user.id,
                email: session.user.email!,
                name: session.user.user_metadata?.full_name || 'User',
                phone: '',
                farmName: '',
                location: '',
              };
              
              setUser(fallbackUser);
              
              const currentUser = await supabaseApi.getCurrentUser(
                session.user.id,
                session.user.email!,
                session.user.user_metadata
              ); 
              console.log('✅ AuthProvider: Profile loaded after sign in:', currentUser?.name);   
              setUser(currentUser);  
              
            } catch (error) {
              console.error('⚠️ AuthProvider: Error getting user after sign in, using fallback:', error);
              // Fallback to basic user info
              const fallbackUser = {
                id: session.user.id,
                email: session.user.email!,
                name: session.user.user_metadata?.full_name || 'User',
                phone: '',
                farmName: '',
                location: '',
              };
              console.log('✅ AuthProvider: Fallback user set after sign in:', fallbackUser.name);
              setUser(fallbackUser);
            } finally {
              // Always set loading to false after handling sign in
              console.log('✅ AuthProvider: Setting loading to false after sign in');
              setIsLoading(false);
            }
          } else if (event === 'SIGNED_OUT') {
            console.log('👋 AuthProvider: User signed out');
            setUser(null);
            setIsLoading(false);
          } else if (event === 'TOKEN_REFRESHED') {
            console.log('🔄 AuthProvider: Token refreshed');
            // Don't change loading state for token refresh
          } else {
            console.log('🔄 AuthProvider: Other auth event:', event);
            // Only set loading to false if we don't have a user yet
            if (!user) {
              console.log('✅ AuthProvider: Setting loading to false for event:', event);
              setIsLoading(false);
            }
          }
        }
      );
      
      subscription = authSubscription;
    }

    return () => {
      console.log('🧹 AuthProvider: Cleanup');
      mounted = false;
      if (subscription) {
        subscription.unsubscribe();
      }
    };
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 AuthProvider: Attempting login...');
      setIsLoading(true);
      
      if (!isSupabaseConfigured()) {
        console.log('🔐 AuthProvider: Demo mode login');
        
        // Demo mode with credential validation
        const validDemoCredentials = [
          { email: 'demo@shetkari.com', password: 'demo123' },
          { email: 'farmer@demo.com', password: 'farmer123' },
          { email: 'test@demo.com', password: 'test123' }
        ];
        
        const isValidCredentials = validDemoCredentials.some(
          cred => cred.email.toLowerCase() === email.toLowerCase() && cred.password === password
        );
        
        if (!isValidCredentials) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Invalid email or password. Try demo@shetkari.com with password: demo123' 
          };
        }
        setUser({
          id: 'demo-user',
          email: email,
          name: 'Demo User',
          phone: '+1-555-0123',
          farmName: 'Demo Farm',
          location: 'Demo Location',
        });
        setIsLoading(false);
        return { success: true };
      }
      
      await supabaseApi.signIn(email, password);
      console.log('✅ AuthProvider: Login successful');
      // Don't set loading to false here - let the auth state change handler do it
      return { success: true };
    } catch (error: any) {
      console.error('❌ AuthProvider: Login error:', error);
      setIsLoading(false);
      
      // Map common supabase auth errors to friendly messages
      const rawMessage = (error?.message || error?.toString() || '').toLowerCase();
      let userMessage = 'Login failed. Please try again.';
      
      if (rawMessage.includes('email not confirmed')) {
        userMessage = 'Please check your email and verify your account before signing in.';
      } else if (rawMessage.includes('invalid login credentials') || rawMessage.includes('invalid credentials')) {
        userMessage = 'Invalid email or password. Please check your credentials and try again.';
      } else if (rawMessage.includes('rate limit') || rawMessage.includes('too many')) {
        userMessage = 'Too many login attempts. Please wait a few minutes and try again.';
      } else if (rawMessage.includes('network') || rawMessage.includes('fetch')) {
        userMessage = 'Network error. Please check your connection and try again.';
      } else if (rawMessage.includes('configuration') || rawMessage.includes('supabase')) {
        userMessage = 'Service configuration error. Please try again later.';
      }
      
      console.error('❌ AuthProvider: Returning error to UI:', userMessage);
      return { success: false, error: userMessage };
    }
  };

  const register = async (email: string, password: string, fullName: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('📝 AuthProvider: Attempting registration...');
      setIsLoading(true);
      
      if (!isSupabaseConfigured()) {
        console.log('📝 AuthProvider: Demo mode registration');
        
        // Demo mode registration with basic validation
        if (password.length < 6) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Password must be at least 6 characters long.' 
          };
        }
        
        if (!email.includes('@') || !email.includes('.')) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Please enter a valid email address.' 
          };
        }
        
        // Simulate existing user check
        const existingDemoEmails = ['demo@shetkari.com', 'farmer@demo.com', 'test@demo.com'];
        if (existingDemoEmails.some(existing => existing.toLowerCase() === email.toLowerCase())) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'An account with this email already exists. Try signing in instead.' 
          };
        }
        setUser({
          id: 'demo-user',
          email: email,
          name: fullName,
          phone: '',
          farmName: '',
          location: '',
        });
        setIsLoading(false);
        return { success: true };
      }
      
      const result = await supabaseApi.signUp(email, password, fullName);
      console.log('✅ AuthProvider: Registration successful');
      // If email confirmation is required, there won't be a session and auth listener won't fire.
      // In that case, stop loading so the UI can prompt the user to verify email.
      if (!result?.session) {
        console.log('📧 AuthProvider: Email confirmation likely required. Stopping loading.');
        setIsLoading(false);
      }
      // If session exists, let the auth state change handler complete the flow.
      return { success: true };
    } catch (error: any) {
      console.error('❌ AuthProvider: Registration error:', error);
      setIsLoading(false);
      
      const rawMessage = (error?.message || error?.toString() || '').toLowerCase();
      let userMessage = 'Registration failed. Please try again.';
      
      if (rawMessage.includes('password should be') || rawMessage.includes('password must')) {
        userMessage = 'Password must be at least 6 characters long.';
      } else if (rawMessage.includes('user already registered') || rawMessage.includes('already registered') || rawMessage.includes('email already')) {
        userMessage = 'An account with this email already exists. Try signing in instead.';
      } else if (rawMessage.includes('invalid email') || rawMessage.includes('email address is invalid')) {
        userMessage = 'Please enter a valid email address.';
      } else if (rawMessage.includes('network') || rawMessage.includes('fetch')) {
        userMessage = 'Network error. Please check your connection and try again.';
      } else if (rawMessage.includes('configuration') || rawMessage.includes('supabase')) {
        userMessage = 'Service configuration error. Please try again later.';
      }
      
      console.error('❌ AuthProvider: Returning error to UI:', userMessage);
      return { success: false, error: userMessage };
    }
  };

  const logout = async (): Promise<void> => {
    try {
      console.log('👋 AuthProvider: Attempting logout...');
      if (isSupabaseConfigured()) {
        await supabaseApi.signOut();
      } else {
        // Demo mode logout
        setUser(null);
        setIsLoading(false);
      }
      console.log('✅ AuthProvider: Logout successful');
    } catch (error: unknown) {
      // Check if the error is due to session not found
      const msg = error instanceof Error ? error.message : String(error || '');
      if (msg.includes('Session from session_id claim in JWT does not exist')) {
        console.warn('⚠️ AuthProvider: Supabase session not found during logout, clearing client session anyway.');
        setUser(null); // Clear user state
      }
      // Always set loading to false after a logout attempt, regardless of error type
      setIsLoading(false);
    }
  };

  console.log('🎯 AuthProvider: Current state - isLoading:', isLoading, 'user:', user?.name || 'none');

  const value = {
    user,
    login,
    register,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};