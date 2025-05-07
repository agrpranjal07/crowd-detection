import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import './App.css';

Chart.register(...registerables);

const formatTime = (timestamp) => {
  const minutes = Math.floor(timestamp / 60);
  const seconds = Math.floor(timestamp % 60);
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

const createDataset = (label, color) => ({
  label,
  data: [],
  borderColor: color,
  backgroundColor: `${color}40`,
  tension: 0.4,
  borderWidth: 2,
  pointRadius: 3,
  fill: false
});

const App = () => {
  const [isAnomaly, setIsAnomaly] = useState(false);
  const [frame, setFrame] = useState('');
  const [charts, setCharts] = useState({
    crowd: { labels: [], datasets: [createDataset('Crowd Density', '#36a2eb')] },
    velocity: { labels: [], datasets: [createDataset('Movement Intensity', '#ff6384')] },
    anomaly: { labels: [], datasets: [createDataset('Anomaly Score', '#9966ff')] }
  });

  const ws = React.useRef(null); 

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8765/ui');
    const MAX_DATA_POINTS = 50;

    const safeUpdate = (prev, chartName, value, timestamp) => {
      const chart = prev[chartName] || { labels: [], datasets: [createDataset('', '#000')] };
      const dataset = chart.datasets[0] || createDataset('', '#000');
      const newLabels = [...chart.labels.slice(-MAX_DATA_POINTS), formatTime(timestamp || 0)];
      const newData = [...(dataset.data || []).slice(-MAX_DATA_POINTS), value || 0];
      return {
        labels: newLabels,
        datasets: [{ ...dataset, data: newData }]
      };
    };
    

    ws.current.onmessage = (event) => {
      try {
        const { frame, analytics } = JSON.parse(event.data);
        // Always update even if frame is empty (to reset UI)
        setFrame(frame ? `data:image/jpeg;base64,${frame}` : '');

        console.log('Received data:', { frame, analytics }); // Debug log
        
    
        setCharts(prev => ({
          crowd: safeUpdate(prev, 'crowd', analytics?.crowd, analytics?.timestamp),
          velocity: safeUpdate(prev, 'velocity', analytics?.velocity, analytics?.timestamp),
          anomaly: safeUpdate(prev, 'anomaly', analytics?.anomaly, analytics?.timestamp)
        }));
        setIsAnomaly(analytics?.is_anomaly || false);
      } catch (error) {
        console.error('Data processing error:', error);
      }
    };
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    ws.current.onopen = () => {
      console.log('WebSocket connection established');
    };

    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close(); // Proper cleanup
      }
    };
  }, []);

  // Determine if latest anomaly exceeds threshold
  //nst latestAnomaly = charts.anomaly.datasets[0].data.slice(-1)[0] || 0;
//const isAnomaly = latestAnomaly > 1.5;

  // Override anomaly chart style when anomaly is true
  const anomalyDataset = charts.anomaly.datasets[0];
  const anomalyChartData = {
    labels: charts.anomaly.labels,
    datasets: [{
      ...anomalyDataset,
      borderColor: isAnomaly ? 'red' : anomalyDataset.borderColor,
      backgroundColor: isAnomaly ? 'rgba(255, 0, 0, 0.3)' : anomalyDataset.backgroundColor,
      pointBackgroundColor: isAnomaly ? 'red' : anomalyDataset.borderColor
    }]
  };
  

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true }
    },
    scales: {
      x: {
        display: true,
        title: { 
          display: true, 
          text: 'Time (MM:SS)',
          color: '#666',
          font: { weight: 'bold', size: 12 }
        },
        grid: { display: false }
      },
      y: {
        beginAtZero: true,
        title: { 
          display: true,
          color: '#666',
          font: { weight: 'bold', size: 12 }
        },
        grace: '10%',
        ticks: { precision: 0 }
      }
    }
  };

  return (
    <div className="app-container">
      <div className="content-wrapper">
        <div className="video-container">
          <img 
            src={frame || null} 
            alt="Live Stream" 
            className="video-frame"
            onError={(e) => e.target.style.display = 'none'}
          />
        </div>
        {isAnomaly && (
          <div className="anomaly-flag" style={{ color: 'red', fontWeight: 'bold', textAlign: 'center', margin: '10px 0' }}>
            Anomaly = true
          </div>
        )}
        <div className="charts-container">
          <div className="chart-box">
            <h3>People Count</h3>
            <div className="chart-area">
              <Line data={charts.crowd} options={chartOptions} />
            </div>
          </div>

          <div className="chart-box">
            <h3>Movement Intensity</h3>
            <div className="chart-area">
              <Line data={charts.velocity} options={chartOptions} />
            </div>
          </div>

          <div className="chart-box">
            <h3>Anomaly Score</h3>
            <div className="chart-area">
              <Line data={anomalyChartData} options={chartOptions} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
