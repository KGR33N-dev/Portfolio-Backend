// API Configuration for kgr33n.com frontend
// Update this file in your Astro project

const isDevelopment = import.meta.env.MODE === 'development';

// EC2 IP: 51.20.78.79 (eu-north-1)
const EC2_IP = '51.20.78.79';

const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000'                    // Local development
  : `http://${EC2_IP}:8000`;                  // Production EC2

export { API_BASE_URL };

// Example usage in your Astro pages:
// 
// ---
// import { API_BASE_URL } from '../config/api.js';
// 
// const response = await fetch(`${API_BASE_URL}/api/blog/?language=en`);
// const { items: posts } = await response.json();
// ---