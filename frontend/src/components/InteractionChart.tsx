import { useEffect, useRef, useContext } from 'react';
import { Card } from 'react-bootstrap';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { PlatformData } from '../types';
import { getPlatformColor, getPlatformDisplayName } from '../utils/platformUtils';
import { ThemeContext } from '../context/ThemeContext';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface InteractionChartProps {
  data: PlatformData[];
  allowedPlatforms?: string[];
}

export const InteractionChart = ({ data, allowedPlatforms = [] }: InteractionChartProps) => {
  const chartRef = useRef<ChartJS>(null);
  const { isDarkMode } = useContext(ThemeContext);
  
  // Filtered data based on allowed platforms
  const filteredData = allowedPlatforms.length 
    ? data.filter(item => allowedPlatforms.includes(item.platform))
    : data;

  // Chart data
  const chartData = {
    labels: filteredData.map(item => getPlatformDisplayName(item.platform)),
    datasets: [
      {
        label: 'Interactions',
        data: filteredData.map(item => item.interactions),
        backgroundColor: filteredData.map(item => getPlatformColor(item.platform, isDarkMode)),
        borderWidth: 0,
        borderRadius: 4,
      },
      {
        label: 'Response Rate %',
        data: filteredData.map(item => Math.round(item.responseRate * 100)),
        backgroundColor: isDarkMode ? 'rgba(255, 206, 86, 0.7)' : 'rgba(255, 193, 7, 0.7)',
        borderWidth: 0,
        borderRadius: 4,
      }
    ]
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          color: isDarkMode ? '#adb5bd' : '#495057',
        }
      },
      x: {
        grid: {
          display: false
        },
        ticks: {
          color: isDarkMode ? '#adb5bd' : '#495057',
        }
      }
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: isDarkMode ? '#dee2e6' : '#212529',
          padding: 20,
        }
      },
      tooltip: {
        backgroundColor: isDarkMode ? 'rgba(33, 37, 41, 0.8)' : 'rgba(255, 255, 255, 0.8)',
        titleColor: isDarkMode ? '#f8f9fa' : '#212529',
        bodyColor: isDarkMode ? '#f8f9fa' : '#212529',
        borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        borderWidth: 1,
      }
    }
  };

  // Update chart if theme changes
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.update();
    }
  }, [isDarkMode]);

  return (
    <Card className="h-100">
      <Card.Header>
        <h5 className="mb-0">Platform Interactions & Response Rates</h5>
      </Card.Header>
      <Card.Body>
        <div style={{ height: '300px' }}>
          <Bar ref={chartRef} data={chartData} options={chartOptions} />
        </div>
      </Card.Body>
    </Card>
  );
};