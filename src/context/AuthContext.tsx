/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { supabaseApi } from '../services/supabaseApi';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
// import { logConfigStatus } from '../utils/configChecker';

interface AuthContextType {
  user: User | null;
  login: (userEmail: string, userPassword: string) => Promise<{ success: boolean; error?: string }>;
  register: (userEmail: string, userPassword: string, userFullName: string) => Promise<{ success: boolean; error?: string }>;
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
    let initTimeout: NodeJS.Timeout | null = null;
    
    console.log('🔄 AuthProvider: Starting initialization...');

    const initializeAuth = async () => {
      try {
        console.log('🔍 AuthProvider: Checking Supabase configuration...');
        
        // Check if Supabase is configured
        if (!isSupabaseConfigured()) {
          console.log('⚠️ AuthProvider: Supabase not configured, using demo mode');
          
          // Check for existing demo session
          const existingDemoUser = localStorage.getItem('demo_user_session');
          if (existingDemoUser && mounted) {
            try {
              const demoUser = JSON.parse(existingDemoUser);
              setUser(demoUser);
              console.log('✅ AuthProvider: Restored demo user from localStorage');
            } catch {
              console.warn('⚠️ AuthProvider: Invalid demo user data in localStorage');
              localStorage.removeItem('demo_user_session');
            }
          }
          
          if (mounted) {
            setIsLoading(false);
            console.log('✅ AuthProvider: Demo mode ready');
          }
          return;
        }

        console.log('🔍 AuthProvider: Getting initial session...');
        
        // Get session with timeout to prevent hanging
        const sessionPromise = supabase.auth.getSession();
        const timeoutPromise = new Promise<never>((_, reject) => {
          initTimeout = setTimeout(() => reject(new Error('Session timeout')), 8000);
        });
        
        const { data: { session }, error } = await Promise.race([
          sessionPromise,
          timeoutPromise
        ]);
        
        if (initTimeout) {
          clearTimeout(initTimeout);
          initTimeout = null;
        }
        
        if (error) {
          console.error('❌ AuthProvider: Error getting session:', error);
          if (mounted) {
            setIsLoading(false);
          }
          return;
        }
        
        console.log('📋 AuthProvider: Session data:', session?.user?.id ? 'User found' : 'No user');
        
        if (session?.user && mounted) {
          console.log('👤 AuthProvider: Loading user profile...');
          try {
            const currentUser = await supabaseApi.getCurrentUser(
              session.user.id,
              session.user.email!,
              session.user.user_metadata
            );
            
            if (currentUser && mounted) {
              console.log('✅ AuthProvider: Profile loaded successfully:', currentUser.name);
              setUser(currentUser);
            }
          } catch (profileError) {
            console.warn('⚠️ AuthProvider: Profile load failed, using fallback');
            if (mounted) {
              setUser({
                id: session.user.id,
                email: session.user.email!,
                name: session.user.user_metadata?.full_name || 'User',
                phone: '',
                farmName: '',
                location: '',
              });
            }
          }
        }
        
        if (mounted) {
          setIsLoading(false);
          console.log('✅ AuthProvider: Initialization complete');
        }
      } catch (initError) {
        console.error('❌ AuthProvider: Initialization error:', initError);
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    // Start initialization immediately
    initializeAuth();

    // Set up auth listener for Supabase
    let authSubscription: { unsubscribe: () => void } | null = null;
    
    if (isSupabaseConfigured()) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          console.log('🔄 Auth event:', event);
          
          if (!mounted) return;
          
          // Handle different auth events
          switch (event) {
            case 'SIGNED_IN':
              if (session?.user) {
                try {
                  const currentUser = await supabaseApi.getCurrentUser(
                    session.user.id,
                    session.user.email!,
                    session.user.user_metadata
                  );
                  if (mounted) {
                    setUser(currentUser);
                  }
                } catch {
                  if (mounted) {
                    setUser({
                      id: session.user.id,
                      email: session.user.email!,
                      name: session.user.user_metadata?.full_name || 'User',
                      phone: '',
                      farmName: '',
                      location: '',
                    });
                  }
                }
              }
              break;
              
            case 'SIGNED_OUT':
              setUser(null);
              localStorage.removeItem('demo_user_session');
              break;
              
            case 'TOKEN_REFRESHED':
              // Don't change user state on token refresh
              break;
          }
        }
      );
      
      authSubscription = subscription;
    }

    return () => {
      mounted = false;
      if (initTimeout) {
        clearTimeout(initTimeout);
      }
      if (authSubscription) {
        authSubscription.unsubscribe();
      }
      console.log('🧹 AuthProvider: Cleanup complete');
    };
  }, []);

  const login = async (userEmail: string, userPassword: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 AuthProvider: Attempting login...');
      setIsLoading(true);
      
      if (!isSupabaseConfigured()) {
        console.log('🔐 AuthProvider: Demo mode login');
        
        // Demo mode with credential validation
        // Demo user credentials
        if (userEmail === 'demo@shetkari.com' && userPassword === 'demo123') {
          const demoUser = {
            id: 'demo-user',
            email: userEmail,
            name: 'Demo User',
            phone: '+1-555-0123',
            farmName: 'Demo Farm',
            location: 'Demo Location',
          };
          setUser(demoUser);
          setIsLoading(false);
          // Save demo session to localStorage for persistence across reloads
          localStorage.setItem('demo_user_session', JSON.stringify(demoUser));
          return { success: true };
        } else {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Invalid email or password. Try demo@shetkari.com with password: demo123' 
          };
        }
      }
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email: userEmail,
        password: userPassword,
      });
      
      console.log('✅ AuthProvider: Login successful');
      
      // Get user profile after successful login
      try {
        const currentUser = await supabaseApi.getCurrentUser(
          data.user!.id,
          data.user!.email!,
          data.user!.user_metadata
        );
        if (currentUser) {
          setUser(currentUser);
          console.log('✅ AuthProvider: User profile loaded after login:', currentUser.name);
        }
      } catch (profileError) {
        console.warn('⚠️ AuthProvider: Could not load profile after login:', profileError);
      }
      
      setIsLoading(false);
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

  const register = async (userEmail: string, userPassword: string, userFullName: string): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('📝 AuthProvider: Attempting registration...');
      setIsLoading(true);
      
      if (!isSupabaseConfigured()) {
        console.log('📝 AuthProvider: Demo mode registration');
        
        // Demo mode registration with basic validation
        if (userPassword.length < 6) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Password must be at least 6 characters long.' 
          };
        }
        
        if (!userEmail.includes('@') || !userEmail.includes('.')) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'Please enter a valid email address.' 
          };
        }
        
        // Simulate existing user check
        const existingDemoEmails = ['demo@shetkari.com', 'farmer@demo.com', 'test@demo.com'];
        if (existingDemoEmails.some(existing => existing.toLowerCase() === userEmail.toLowerCase())) {
          setIsLoading(false);
          return { 
            success: false, 
            error: 'An account with this email already exists. Try signing in instead.' 
          };
        }
        const newDemoUser = {
          id: 'demo-user',
          email: userEmail,
          name: userFullName,
          phone: '',
          farmName: '',
          location: '',
        };
        setUser(newDemoUser);
        setIsLoading(false);
        // Save demo session to localStorage for persistence across reloads
        localStorage.setItem('demo_user_session', JSON.stringify(newDemoUser));
        return { success: true };
      }
      
      const { data, error } = await supabase.auth.signUp({
        email: userEmail,
        password: userPassword,
        options: {
          data: {
            full_name: userFullName,
          },
        },
      });
      
      if (error) {
        console.error('❌ AuthProvider: Registration error:', error);
        setIsLoading(false);
        return { 
          success: false, 
          error: error.message || 'Registration failed. Please try again.' 
        };
      }
      
      console.log('✅ AuthProvider: Registration successful');
      // If email confirmation is required, there won't be a session and auth listener won't fire.
      // In that case, stop loading so the UI can prompt the user to verify email.
      if (!data.session) {
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
      console.log('🚪 AuthProvider: Logging out...');
      
      // Clear demo session if it exists
      localStorage.removeItem('demo_user_session');
      
      if (isSupabaseConfigured()) {
        await supabase.auth.signOut();
        console.log('✅ AuthProvider: Supabase signout successful');
      }
      
      setUser(null);
      console.log('✅ AuthProvider: Logout successful');
    } catch (error) {
      console.error('❌ AuthProvider: Logout error:', error);
      // Clear user state even if logout fails
      localStorage.removeItem('demo_user_session');
      setUser(null);
    } finally {
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