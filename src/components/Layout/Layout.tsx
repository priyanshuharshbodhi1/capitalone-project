import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from './Navbar';

const Layout: React.FC = () => {
  const location = useLocation();
  const isMockSensor = location.pathname.includes('/mock-sensor');

  return (
    <div className={isMockSensor ? 'min-h-screen bg-red-50' : 'min-h-screen bg-gray-50'}>
      {!isMockSensor && <Navbar />}
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;