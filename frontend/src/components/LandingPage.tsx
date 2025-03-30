import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { FaRobot, FaComments, FaDatabase, FaChartLine, FaLock } from 'react-icons/fa';
import { BiSolidBrain } from 'react-icons/bi';
import '../styles/LandingPage.css';

const LandingPage: React.FC = () => {
  const handleGetStarted = () => {
    // For the landing page demo, we'll just change the window location
    window.location.href = '/login';
  };
  
  const handleWatchDemo = () => {
    // For demo purposes
    alert('Demo video coming soon!');
  };
  
  const animationRef = useRef<HTMLDivElement>(null);
  const animationInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (animationRef.current) {
      // Create a scene
      const scene = new THREE.Scene();
      
      // Create a camera
      const camera = new THREE.PerspectiveCamera(
        75,
        animationRef.current.clientWidth / animationRef.current.clientHeight,
        0.1,
        1000
      );
      camera.position.z = 5;
      
      // Create a renderer
      const renderer = new THREE.WebGLRenderer({ alpha: true });
      renderer.setSize(animationRef.current.clientWidth, animationRef.current.clientHeight);
      renderer.setClearColor(0x000000, 0);
      
      // Clear any existing canvases
      if (animationRef.current.querySelector('canvas')) {
        animationRef.current.querySelector('canvas')?.remove();
      }
      
      animationRef.current.appendChild(renderer.domElement);
      
      // Create a geometry (sphere with lots of segments for smoothness)
      const geometry = new THREE.SphereGeometry(2, 32, 32);
      
      // Create a material
      const material = new THREE.MeshBasicMaterial({
        color: 0x6a55fa,
        wireframe: true,
        transparent: true,
        opacity: 0.7
      });
      
      // Create a mesh
      const sphere = new THREE.Mesh(geometry, material);
      scene.add(sphere);
      
      // Create particles
      const particlesGeometry = new THREE.BufferGeometry();
      const particlesCount = 500;
      
      const posArray = new Float32Array(particlesCount * 3);
      for (let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 10;
      }
      
      particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      
      const particlesMaterial = new THREE.PointsMaterial({
        size: 0.02,
        color: 0xffffff,
        transparent: true,
        opacity: 0.8
      });
      
      const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
      scene.add(particlesMesh);
      
      // Animation
      const animate = () => {
        sphere.rotation.x += 0.003;
        sphere.rotation.y += 0.003;
        
        particlesMesh.rotation.x += 0.0005;
        particlesMesh.rotation.y += 0.0005;
        
        renderer.render(scene, camera);
        animationInstanceRef.current = requestAnimationFrame(animate);
      };
      
      animate();
      
      // Handle resize
      const handleResize = () => {
        if (animationRef.current) {
          camera.aspect = animationRef.current.clientWidth / animationRef.current.clientHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(animationRef.current.clientWidth, animationRef.current.clientHeight);
        }
      };
      
      window.addEventListener('resize', handleResize);
      
      // Clean up
      return () => {
        window.removeEventListener('resize', handleResize);
        if (animationInstanceRef.current) {
          cancelAnimationFrame(animationInstanceRef.current);
        }
        renderer.dispose();
      };
    }
  }, []);

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-6 col-md-12 text-light">
              <h1 className="display-4 fw-bold mb-4">Meet Dana AI</h1>
              <p className="fs-5 mb-4">
                The intelligent platform that transforms how businesses communicate with customers.
                Powered by advanced AI to enhance customer support, knowledge management, and team collaboration.
              </p>
              <div className="d-flex flex-wrap gap-3">
                <button 
                  className="btn btn-primary btn-lg" 
                  onClick={handleGetStarted}
                >
                  Get Started
                </button>
                <button 
                  className="btn btn-outline-light btn-lg"
                  onClick={handleWatchDemo}
                >
                  Watch Demo
                </button>
              </div>
            </div>
            <div className="col-lg-6 col-md-12">
              <div ref={animationRef} className="animation-container" style={{ height: '400px' }}></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features py-5">
        <div className="container">
          <div className="text-center mb-5">
            <h2 className="display-5 fw-bold">Supercharge Your Customer Interactions</h2>
            <p className="fs-5">Dana AI combines powerful tools to help you deliver exceptional service</p>
          </div>
          
          <div className="row g-4">
            {[
              {
                icon: <div className="feature-icon"><BiSolidBrain size={30} /></div>,
                title: "Intelligent Responses",
                description: "Generate contextual and personalized responses to customer inquiries in seconds."
              },
              {
                icon: <div className="feature-icon"><FaComments size={30} /></div>,
                title: "Omnichannel Support",
                description: "Connect with customers across Slack, email, social media, and more from a single interface."
              },
              {
                icon: <div className="feature-icon"><FaDatabase size={30} /></div>,
                title: "Knowledge Management",
                description: "Organize and retrieve information from documents, PDFs, and other sources with ease."
              },
              {
                icon: <div className="feature-icon"><FaRobot size={30} /></div>,
                title: "Workflow Automation",
                description: "Automate repetitive tasks and create custom workflows tailored to your business needs."
              },
              {
                icon: <div className="feature-icon"><FaChartLine size={30} /></div>,
                title: "Advanced Analytics",
                description: "Gain insights into customer interactions and team performance with detailed metrics."
              },
              {
                icon: <div className="feature-icon"><FaLock size={30} /></div>,
                title: "Enterprise-Grade Security",
                description: "Keep your data secure with advanced encryption and role-based access controls."
              }
            ].map((feature, index) => (
              <div key={index} className="col-md-6 col-lg-4">
                <div className="card h-100 border-0 shadow-sm">
                  <div className="card-body d-flex flex-column align-items-center text-center p-4">
                    <div className="feature-icon-wrapper mb-3">
                      {feature.icon}
                    </div>
                    <h3 className="card-title h5 fw-bold">{feature.title}</h3>
                    <p className="card-text">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="use-cases py-5">
        <div className="container">
          <div className="text-center mb-5">
            <h2 className="display-5 fw-bold">Real-World Applications</h2>
            <p className="fs-5">See how Dana AI is transforming businesses across industries</p>
          </div>
          
          <div className="row g-4">
            {[
              {
                title: "Customer Support",
                description: "Reduce response times by 73% while increasing customer satisfaction scores. Dana AI helps your team provide faster, more accurate support.",
                gradient: "bg-gradient-primary"
              },
              {
                title: "Sales Enablement",
                description: "Equip your sales team with instant access to product information, competitive insights, and personalized messaging that converts leads.",
                gradient: "bg-gradient-info"
              },
              {
                title: "Internal Knowledge Base",
                description: "Centralize company knowledge and make it accessible to your team. Dana AI helps employees find the information they need, when they need it.",
                gradient: "bg-gradient-success"
              }
            ].map((useCase, index) => (
              <div key={index} className="col-md-4">
                <div className={`card h-100 border-0 ${useCase.gradient} text-white`}>
                  <div className="card-body p-4">
                    <h3 className="card-title h4 fw-bold">{useCase.title}</h3>
                    <p className="card-text">{useCase.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="integrations py-5">
        <div className="container">
          <div className="text-center mb-5">
            <h2 className="display-5 fw-bold">Seamless Integrations</h2>
            <p className="fs-5">Connect Dana AI with your favorite tools and platforms</p>
          </div>
          
          <div className="row justify-content-center">
            <div className="col-lg-8">
              <div className="d-flex flex-wrap justify-content-center gap-4">
                {['Slack', 'Gmail', 'Outlook', 'Zendesk', 'Salesforce', 'Shopify', 'HubSpot', 'Google Analytics'].map((integration, index) => (
                  <div key={index} className="integration-pill">
                    {integration}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta py-5">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <h2 className="display-5 fw-bold mb-4">Ready to Transform Your Customer Experience?</h2>
              <p className="fs-5 mb-4">
                Join businesses that are using Dana AI to deliver exceptional service and grow their customer relationships.
              </p>
              <button 
                className="btn btn-primary btn-lg px-5 py-3"
                onClick={handleGetStarted}
              >
                Start Your Free Trial
              </button>
              <p className="mt-3 text-muted">No credit card required. 14-day free trial.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;