import { useEffect, useRef, useContext } from 'react';
import * as THREE from 'three';
import { ThemeContext } from '../context/ThemeContext';

export const DashboardBackground = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { isDarkMode } = useContext(ThemeContext);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Create scene, camera, and renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    containerRef.current.appendChild(renderer.domElement);
    
    // Create shapes
    const shapes: THREE.Mesh[] = [];
    const colors = isDarkMode 
      ? ['#1877F2', '#E1306C', '#25D366', '#4A154B', '#00B2FF'] // Dark mode colors
      : ['#1877F2', '#C13584', '#25D366', '#611f69', '#0078D4']; // Light mode colors
    
    const createShape = (color: string, size: number, x: number, y: number, z: number) => {
      const geometry = new THREE.SphereGeometry(size, 24, 24);
      const material = new THREE.MeshBasicMaterial({ 
        color: new THREE.Color(color),
        transparent: true,
        opacity: 0.6
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(x, y, z);
      
      // Add some random movement values to each shape
      (mesh as any).movement = {
        x: (Math.random() - 0.5) * 0.01,
        y: (Math.random() - 0.5) * 0.01,
        z: (Math.random() - 0.5) * 0.01
      };
      
      return mesh;
    };
    
    // Create multiple shapes with different positions
    for (let i = 0; i < 8; i++) {
      const x = (Math.random() - 0.5) * 10;
      const y = (Math.random() - 0.5) * 10;
      const z = (Math.random() - 0.5) * 5 - 5; // Keep all shapes behind the content
      const size = Math.random() * 0.5 + 0.5;
      const color = colors[Math.floor(Math.random() * colors.length)];
      
      const shape = createShape(color, size, x, y, z);
      shapes.push(shape);
      scene.add(shape);
    }
    
    // Position camera
    camera.position.z = 5;
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Animate each shape
      shapes.forEach(shape => {
        // Make shapes bounce within boundaries
        if (shape.position.x > 5 || shape.position.x < -5) {
          (shape as any).movement.x *= -1;
        }
        if (shape.position.y > 5 || shape.position.y < -5) {
          (shape as any).movement.y *= -1;
        }
        
        // Update positions
        shape.position.x += (shape as any).movement.x;
        shape.position.y += (shape as any).movement.y;
        shape.position.z += (shape as any).movement.z;
        
        // Rotate shapes
        shape.rotation.x += 0.005;
        shape.rotation.y += 0.005;
      });
      
      renderer.render(scene, camera);
    };
    
    animate();
    
    // Handle window resize
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    
    window.addEventListener('resize', handleResize);
    
    // Cleanup
    return () => {
      if (containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
      window.removeEventListener('resize', handleResize);
    };
  }, [isDarkMode]); // Re-initialize when theme changes
  
  return (
    <div 
      ref={containerRef} 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none'
      }}
    />
  );
};