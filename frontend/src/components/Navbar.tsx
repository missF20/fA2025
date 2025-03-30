import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

interface NavbarProps {
  transparent?: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ transparent = true }) => {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const navbarClasses = `fixed top-0 left-0 right-0 z-50 py-3 transition-all duration-300 ${
    transparent && !scrolled 
      ? 'bg-transparent backdrop-blur-0' 
      : scrolled 
        ? 'bg-white/90 backdrop-blur-md shadow-sm py-2' 
        : 'bg-white/90 backdrop-blur-md'
  }`;

  const navLinkClasses = `nav-link ${
    transparent && !scrolled 
      ? 'text-white hover:text-white/80' 
      : 'text-gray-800 hover:text-primary'
  }`;

  const handleLogoClick = () => {
    navigate('/');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <nav className={navbarClasses}>
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <div 
            className="text-xl font-bold cursor-pointer flex items-center" 
            onClick={handleLogoClick}
          >
            <span className={transparent && !scrolled ? 'text-white' : 'text-primary'}>
              Dana AI
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <ul className="flex space-x-6">
              <li><a href="#features" className={navLinkClasses}>Features</a></li>
              <li><a href="#use-cases" className={navLinkClasses}>Use Cases</a></li>
              <li><a href="#integrations" className={navLinkClasses}>Integrations</a></li>
              <li><a href="#testimonials" className={navLinkClasses}>Testimonials</a></li>
            </ul>
            <div className="flex items-center space-x-4">
              <button 
                className="btn btn-sm btn-outline-primary"
                onClick={() => handleNavigation('/login')}
              >
                Log In
              </button>
              <button 
                className="btn btn-sm btn-primary"
                onClick={() => handleNavigation('/signup')}
              >
                Sign Up Free
              </button>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className={`focus:outline-none ${transparent && !scrolled ? 'text-white' : 'text-gray-800'}`}
            >
              {isMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden mt-4 py-4 bg-white/95 backdrop-blur-md shadow-lg rounded-lg">
            <ul className="flex flex-col space-y-4 px-4">
              <li>
                <a 
                  href="#features" 
                  className="text-gray-800 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Features
                </a>
              </li>
              <li>
                <a 
                  href="#use-cases" 
                  className="text-gray-800 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Use Cases
                </a>
              </li>
              <li>
                <a 
                  href="#integrations" 
                  className="text-gray-800 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Integrations
                </a>
              </li>
              <li>
                <a 
                  href="#testimonials" 
                  className="text-gray-800 hover:text-primary"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Testimonials
                </a>
              </li>
            </ul>
            <div className="mt-4 px-4 pt-4 border-t border-gray-100 flex flex-col space-y-3">
              <button 
                className="btn btn-sm btn-outline-primary w-full"
                onClick={() => {
                  handleNavigation('/login');
                  setIsMenuOpen(false);
                }}
              >
                Log In
              </button>
              <button 
                className="btn btn-sm btn-primary w-full"
                onClick={() => {
                  handleNavigation('/signup');
                  setIsMenuOpen(false);
                }}
              >
                Sign Up Free
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;