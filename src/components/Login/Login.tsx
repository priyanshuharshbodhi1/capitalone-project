import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { Leaf, Mail, Lock, Loader2, User } from 'lucide-react';
import toast from 'react-hot-toast';

const Login: React.FC = () => {
  const { t } = useTranslation();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('Bolt1234');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const { login, register, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password || (!isLoginMode && !fullName)) {
      toast.error(t('auth.fillAllFields'));
      setError(t('auth.fillAllFields'));
      return;
    }

    try {
      if (isLoginMode) {
        const res = await login(email, password);
        if (!res.success) {
          const errorMessage = res.error || t('auth.loginError');
          toast.error(errorMessage);
          setError(errorMessage);
          return;
        }
        toast.success(t('auth.loginSuccess'));
      } else {
        const res = await register(email, password, fullName);
        if (!res.success) {
          const errorMessage = res.error || t('auth.registerError');
          toast.error(errorMessage);
          setError(errorMessage);
          return;
        }
        toast.success(t('auth.registerSuccess'));
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('auth.unexpectedError');
      toast.error(errorMessage);
      setError(errorMessage);
    }
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setError('');
    setEmail('');
    setPassword('');
    setFullName('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-emerald-500 p-3 rounded-full">
              <Leaf className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
            </div>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">{t('app.name')}</h2>
          <p className="mt-2 text-gray-600 text-sm sm:text-base">{t('app.subtitle')}</p>
        </div>

        <div className="bg-white shadow-2xl rounded-2xl p-6 sm:p-8">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900 text-center">
              {isLoginMode ? t('auth.loginTitle') : t('auth.registerTitle')}
            </h3>
            <p className="text-gray-600 text-sm text-center mt-1">
              {isLoginMode ? t('auth.loginSubtitle') : t('auth.registerSubtitle')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLoginMode && (
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.fullName')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                  </div>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                    placeholder={t('auth.enterFullName')}
                    disabled={isLoading}
                  />
                </div>
              </div>
            )}

                          <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.email')}
                </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                  placeholder={t('auth.enterEmail')}
                  disabled={isLoading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                {t('common.password')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 sm:pl-10 pr-3 py-2 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 text-sm sm:text-base"
                  placeholder={t('auth.enterPassword')}
                  disabled={isLoading}
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-600 text-sm font-medium">{error}</p>
              </div>
            )}



            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 sm:py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-2 sm:mr-3 h-4 w-4 sm:h-5 sm:w-5" />
                  {isLoginMode ? t('auth.signIn') + '...' : t('auth.createAccount') + '...'}
                </>
              ) : (
                isLoginMode ? t('auth.signIn') : t('auth.createAccount')
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={toggleMode}
              className="text-emerald-600 hover:text-emerald-700 font-medium text-sm transition-colors duration-200"
            >
              {isLoginMode 
                ? t('auth.dontHaveAccount') + ' ' + t('auth.signUp')
                : t('auth.alreadyHaveAccount') + ' ' + t('auth.signIn')
              }
            </button>
          </div>
        </div>
      </div>
      
    </div>
  );
};

export default Login;
