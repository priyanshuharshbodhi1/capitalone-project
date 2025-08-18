import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import { Tractor, LayoutDashboard, Settings, LogOut, User, PieChart, Menu, X, MessageSquare, ChevronDown, Leaf } from 'lucide-react';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const navigation = [
    { name: t('navigation.assistant'), href: '/', icon: MessageSquare },
    { name: t('navigation.plantdoc'), href: '/plantdoc', icon: Leaf },
    { name: t('navigation.dashboard'), href: '/dashboard', icon: LayoutDashboard },
    { name: t('navigation.analytics'), href: '/analytics', icon: PieChart },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <div className="bg-emerald-500 p-2 rounded-lg">
              <Tractor className="h-6 w-6 text-white" />
            </div>
            <span className="ml-2 text-xl font-bold text-gray-900">{t('app.name')}</span>
          </div>
          
          {/* Centered Navigation Tabs */}
          <div className="hidden md:flex items-center justify-center flex-1">
            <div className="bg-gray-100 p-1 rounded-xl flex space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive(item.href)
                        ? 'bg-white text-emerald-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Profile Avatar + Dropdown */}
          <div className="hidden md:flex md:items-center">
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 focus:outline-none transition-colors duration-200"
              >
                <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-emerald-600" />
                </div>
                <span>{user?.name}</span>
                <ChevronDown className="h-4 w-4 text-gray-400" />
              </button>
              
              {/* Profile Dropdown */}
              {isProfileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50 border border-gray-200">
                  <Link
                    to="/settings"
                    onClick={() => setIsProfileDropdownOpen(false)}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                  >
                    <Settings className="h-4 w-4 mr-3" />
                    {t('navigation.settings')}
                  </Link>
                  <button
                    onClick={() => {
                      logout();
                      setIsProfileDropdownOpen(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors duration-200"
                  >
                    <LogOut className="h-4 w-4 mr-3" />
                    {t('common.logout')}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-emerald-500 transition-colors duration-200"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-200 shadow-lg">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={closeMobileMenu}
                  className={`flex items-center px-3 py-3 rounded-md text-base font-medium transition-colors duration-200 ${
                    isActive(item.href)
                      ? 'text-emerald-600 bg-emerald-50 border-l-4 border-emerald-500'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </div>
          
          {/* Mobile User Section */}
          <div className="pt-4 pb-3 border-t border-gray-200">
            <div className="flex items-center px-5 mb-3">
              <div className="flex items-center space-x-3">
                <div className="bg-emerald-100 p-2 rounded-full">
                  <User className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <div className="text-base font-medium text-gray-800">{user?.name}</div>
                  <div className="text-sm text-gray-500">{user?.email}</div>
                </div>
              </div>
            </div>
            <div className="px-2 space-y-1">
              <Link
                to="/settings"
                onClick={closeMobileMenu}
                className={`flex items-center px-3 py-3 rounded-md text-base font-medium transition-colors duration-200 ${
                  isActive('/settings')
                    ? 'text-emerald-600 bg-emerald-50 border-l-4 border-emerald-500'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Settings className="h-5 w-5 mr-3" />
                {t('navigation.settings')}
              </Link>
              <button
                onClick={() => {
                  logout();
                  closeMobileMenu();
                }}
                className="flex items-center w-full px-3 py-3 rounded-md text-base font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors duration-200"
              >
                <LogOut className="h-5 w-5 mr-3" />
                {t('common.logout')}
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;