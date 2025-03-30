import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import '../styles/LandingPage.css';

// FloatingFeature component with bouncing effect
const FloatingFeature: React.FC<{ position?: string; delay?: number; size?: string }> = ({ 
  position = 'right', 
  delay = 0,
  size = 'w-72 h-72'
}) => (
  <motion.div
    className={`absolute ${position === 'left' ? 'left-5' : position === 'right' ? 'right-5' : 'left-1/2 -translate-x-1/2'} z-0 ${size}`}
    initial={{ y: 0 }}
    animate={{ y: [0, -20, 0] }}
    transition={{
      duration: 4,
      delay: delay,
      repeat: Infinity,
      ease: "easeInOut"
    }}
  >
    <div className="relative w-full h-full">
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-full blur-xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0.8, 0.5],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute inset-0 border-2 border-blue-500/20 rounded-full"
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
      />
      <motion.div
        className="absolute inset-0 border-2 border-purple-500/20 rounded-full"
        animate={{
          rotate: [360, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "linear"
        }}
      />
    </div>
  </motion.div>
);

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  
  const handleGetStarted = () => {
    // Navigate to login page
    navigate('/login');
  };
  
  const handleWatchDemo = () => {
    // For demo purposes
    alert('Demo video coming soon!');
  };
  
  const animationRef = useRef<HTMLDivElement>(null);
  const animationInstanceRef = useRef<any>(null);
  
  // Refs for positioning floating features
  const featuresRef = useRef<HTMLDivElement>(null);
  const integrationsRef = useRef<HTMLDivElement>(null);
  const testimonialsRef = useRef<HTMLDivElement>(null);

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
              <h1 className="display-4 fw-bold mb-4">Transform Customer Experiences with Dana AI</h1>
              <p className="fs-5 mb-4">
                The intelligent platform that revolutionizes how businesses interact with customers.
                Harness the power of AI to deliver exceptional support, manage knowledge efficiently, and boost team collaboration.
              </p>
              <div className="d-flex flex-wrap gap-3 hero-buttons">
                <button 
                  className="btn btn-primary btn-lg cta-button" 
                  onClick={handleGetStarted}
                >
                  Start Free Trial
                </button>
                <button 
                  className="btn btn-outline-light btn-lg"
                  onClick={handleWatchDemo}
                >
                  Watch Demo
                </button>
              </div>
              <div className="mt-4 d-flex align-items-center opacity-75">
                <span className="me-2">Trusted by 500+ businesses</span>
                <div className="d-flex align-items-center">
                  <span className="badge bg-light text-dark me-2">⭐⭐⭐⭐⭐</span>
                  <span>4.9/5 rating</span>
                </div>
              </div>
            </div>
            <div className="col-lg-6 col-md-12">
              <div ref={animationRef} className="animation-container"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features position-relative" ref={featuresRef}>
        {/* Animated floating feature */}
        <FloatingFeature position="left" delay={0.5} size="w-64 h-64" />
        
        <div className="container">
          <div className="text-center mb-5 section-heading">
            <h2 className="display-5 fw-bold">Supercharge Your Customer Interactions</h2>
            <p className="fs-5 text-muted mx-auto" style={{ maxWidth: "700px" }}>
              Dana AI combines powerful tools that help businesses deliver exceptional service and build lasting customer relationships
            </p>
          </div>
          
          <div className="row g-4">
            {[
              {
                icon: <div className="feature-icon">AI</div>,
                title: "Intelligent Responses",
                description: "Generate contextual and personalized responses to customer inquiries in seconds, ensuring accuracy and consistency."
              },
              {
                icon: <div className="feature-icon">CM</div>,
                title: "Omnichannel Support",
                description: "Connect with customers across Slack, email, social media, and more from a single unified interface."
              },
              {
                icon: <div className="feature-icon">DB</div>,
                title: "Knowledge Management",
                description: "Organize and retrieve information from documents, PDFs, and various sources with powerful search capabilities."
              },
              {
                icon: <div className="feature-icon">AT</div>,
                title: "Workflow Automation",
                description: "Automate repetitive tasks and create custom workflows tailored to your specific business needs."
              },
              {
                icon: <div className="feature-icon">CH</div>,
                title: "Advanced Analytics",
                description: "Gain actionable insights into customer interactions and team performance with detailed metrics and reports."
              },
              {
                icon: <div className="feature-icon">LK</div>,
                title: "Enterprise-Grade Security",
                description: "Keep your data secure with advanced encryption, role-based access controls, and compliance tools."
              }
            ].map((feature, index) => (
              <div key={index} className="col-md-6 col-lg-4 mb-4">
                <div className="feature-card card h-100 border-0 shadow-sm">
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
      <section className="use-cases">
        <div className="container">
          <div className="text-center mb-5 section-heading">
            <h2 className="display-5 fw-bold">Real-World Applications</h2>
            <p className="fs-5 text-muted mx-auto" style={{ maxWidth: "700px" }}>
              See how Dana AI is transforming businesses across industries
            </p>
          </div>
          
          <div className="row g-4">
            {[
              {
                title: "Customer Support",
                description: "Reduce response times by 73% while increasing customer satisfaction scores. Dana AI helps your team provide faster, more accurate support.",
                stats: { metric: "73%", label: "Faster Response Time" },
                icon: "🎧",
                gradient: "bg-gradient-primary"
              },
              {
                title: "Sales Enablement",
                description: "Equip your sales team with instant access to product information, competitive insights, and personalized messaging that converts leads.",
                stats: { metric: "41%", label: "Increased Conversions" },
                icon: "💼",
                gradient: "bg-gradient-info"
              },
              {
                title: "Internal Knowledge Base",
                description: "Centralize company knowledge and make it accessible to your team. Dana AI helps employees find the information they need, when they need it.",
                stats: { metric: "85%", label: "Faster Information Retrieval" },
                icon: "📚",
                gradient: "bg-gradient-success"
              }
            ].map((useCase, index) => (
              <div key={index} className="col-md-4">
                <div className={`use-case-card card h-100 border-0 ${useCase.gradient} text-white`}>
                  <div className="card-body p-4">
                    <div className="d-flex align-items-center mb-3">
                      <span className="display-6 me-2">{useCase.icon}</span>
                      <h3 className="card-title h4 fw-bold mb-0">{useCase.title}</h3>
                    </div>
                    <p className="card-text mb-4">{useCase.description}</p>
                    <div className="d-flex align-items-center mt-auto">
                      <div className="display-5 fw-bold me-3">{useCase.stats.metric}</div>
                      <div className="fs-6 opacity-75">{useCase.stats.label}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="text-center mt-5">
            <button className="btn btn-outline-primary btn-lg" onClick={handleGetStarted}>
              Explore All Use Cases
            </button>
          </div>
        </div>
      </section>

      {/* Integration Section */}
      <section className="integrations position-relative" ref={integrationsRef}>
        {/* Animated floating feature */}
        <FloatingFeature position="right" delay={1} size="w-80 h-80" />
        
        <div className="container">
          <div className="text-center mb-5 section-heading">
            <h2 className="display-5 fw-bold">Seamless Integrations</h2>
            <p className="fs-5 text-muted mx-auto" style={{ maxWidth: "700px" }}>
              Connect Dana AI with your favorite tools and platforms to create a unified workflow
            </p>
          </div>
          
          <div className="row justify-content-center">
            <div className="col-lg-10">
              <div className="integration-container">
                <div className="d-flex flex-wrap justify-content-center gap-4">
                  {[
                    { name: 'Slack', icon: '💬' },
                    { name: 'Gmail', icon: '📧' },
                    { name: 'Outlook', icon: '✉️' },
                    { name: 'Zendesk', icon: '🎯' },
                    { name: 'Salesforce', icon: '☁️' },
                    { name: 'Shopify', icon: '🛒' },
                    { name: 'HubSpot', icon: '📊' },
                    { name: 'Google Analytics', icon: '📈' }
                  ].map((integration, index) => (
                    <div key={index} className="integration-pill">
                      <span className="me-2">{integration.icon}</span> {integration.name}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="testimonials position-relative" ref={testimonialsRef}>
        {/* Animated floating feature */}
        <FloatingFeature position="center" delay={1.5} size="w-96 h-96" />
        
        <div className="container">
          <div className="text-center mb-5 section-heading">
            <h2 className="display-5 fw-bold">What Our Customers Say</h2>
            <p className="fs-5 text-muted mx-auto" style={{ maxWidth: "700px" }}>
              Hear from businesses that have transformed their customer experience with Dana AI
            </p>
          </div>

          <div className="row g-4">
            {[
              {
                quote: "Dana AI has revolutionized how we handle customer inquiries. Response times are down 65% and customer satisfaction is up 40%.",
                author: "Sarah Johnson",
                position: "Customer Support Director",
                company: "TechNova Solutions"
              },
              {
                quote: "The knowledge management system is a game-changer. Our team can instantly access critical information, making onboarding new staff so much easier.",
                author: "Michael Chen",
                position: "Operations Manager",
                company: "GrowthForce Marketing"
              },
              {
                quote: "Integrating Dana AI with our existing tools was seamless. The Slack integration alone has saved our team countless hours every week.",
                author: "Jessica Rodriguez",
                position: "Chief Technology Officer",
                company: "Elevate Retail"
              }
            ].map((testimonial, index) => (
              <div key={index} className="col-md-4">
                <div className="testimonial-card h-100">
                  <div className="testimonial-quote">"</div>
                  <p className="mb-4 fs-5">{testimonial.quote}</p>
                  <div className="d-flex align-items-center mt-auto">
                    <div className="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" style={{ width: "50px", height: "50px", fontSize: "1.25rem" }}>
                      {testimonial.author.charAt(0)}
                    </div>
                    <div className="ms-3">
                      <h5 className="mb-0">{testimonial.author}</h5>
                      <p className="text-muted mb-0">{testimonial.position}, {testimonial.company}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <h2 className="display-5 fw-bold mb-4">Ready to Transform Your Customer Experience?</h2>
              <p className="fs-5 mb-5">
                Join hundreds of businesses that are using Dana AI to deliver exceptional service and grow their customer relationships.
              </p>
              <button 
                className="btn btn-primary btn-lg px-5 py-3 cta-button"
                onClick={handleGetStarted}
              >
                Start Your Free Trial
              </button>
              <p className="mt-4 text-light opacity-75">No credit card required. 14-day free trial.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;