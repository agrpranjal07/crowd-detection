import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import { 
  Chart, 
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

const MAX_DATA_POINTS = 50;
const UPDATE_INTERVAL = 100; // 100ms between updates

const App = () => {
  const [frame, setFrame] = useState('');
  const [metrics, setMetrics] = useState({
    count: [],
    density: [],
    velocity: [],
    timestamps: []
  });
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  
  const wsRef = useRef(null);
  const chartRef = useRef(null);
  const dataQueue = useRef([]);
  const updateTimer = useRef(null);
  const isMounted = useRef(true);

  // Batched updates using interval
  const processQueue = useCallback(() => {
    if (!isMounted.current || dataQueue.current.length === 0) return;

    const batch = dataQueue.current.splice(0, 10); // Process up to 10 messages
    const lastData = batch[batch.length - 1];

    setMetrics(prev => ({
      count: [...prev.count.slice(-MAX_DATA_POINTS), ...batch.map(d => d.analytics.count)],
      density: [...prev.density.slice(-MAX_DATA_POINTS), ...batch.map(d => d.analytics.density)],
      velocity: [...prev.velocity.slice(-MAX_DATA_POINTS), ...batch.map(d => d.analytics.velocity)],
      timestamps: [...prev.timestamps.slice(-MAX_DATA_POINTS), ...batch.map(d => new Date(d.analytics.timestamp))]
    }));

    setFrame(`data:image/jpeg;base64,${lastData.frame}`);
  }, []);

  useEffect(() => {
    isMounted.current = true;
    
    // WebSocket connection
    wsRef.current = new WebSocket('ws://localhost:8766');

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        dataQueue.current.push(data);
      } catch (error) {
        console.error('Message processing error:', error);
      }
    };

    // Setup WebSocket handlers
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      updateTimer.current = setInterval(processQueue, UPDATE_INTERVAL);
    };

    wsRef.current.onmessage = handleMessage;
    wsRef.current.onclose = () => setConnectionStatus('disconnected');
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    // Cleanup
    return () => {
      isMounted.current = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (updateTimer.current) {
        clearInterval(updateTimer.current);
      }
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [processQueue]);

  // Chart configuration
  const chartOptions = useRef({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: true,
        mode: 'nearest',
        intersect: false
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'second',
          tooltipFormat: 'HH:mm:ss',
          displayFormats: {
            second: 'HH:mm:ss'
          }
        },
        title: {
          display: true,
          text: 'Time'
        },
        grid: {
          display: false
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value'
        },
        beginAtZero: true,
        ticks: {
          precision: 0
        }
      }
    }
  }).current;

  // In App component return statement
return (
  <div className="dashboard">
    <div className="status-bar">
      <div className={`connection-status ${connectionStatus}`}>
        Status: {connectionStatus.toUpperCase()}
      </div>
      <div className="metrics-preview">
        <span>People: {metrics.count.slice(-1)[0] || 0}</span>
        <span>Density: {(metrics.density.slice(-1)[0] || 0).toFixed(2)}</span>
        <span>Velocity: {(metrics.velocity.slice(-1)[0] || 0).toFixed(1)} px/f</span>
      </div>
    </div>

    <div className="content-wrapper">
      <div className="video-container">
        {frame ? (
          <img 
            src={frame} 
            alt="Live Feed" 
            className="video-feed"
            key={metrics.timestamps.length}
          />
        ) : (
          <div className="video-placeholder">
            <div className="loading-spinner"></div>
            <p>Awaiting video stream...</p>
          </div>
        )}
      </div>

      <div className="charts-container">
        <div className="chart-wrapper">
          <h3>Human Count</h3>
          <Line
            data={{
              labels: metrics.timestamps,
              datasets: [{
                label: 'Human Count',
                data: metrics.count,
                borderColor: '#4bc0c0',
                pointRadius: 0
              }]
            }}
            options={chartOptions}
          />
        </div>

        <div className="chart-wrapper">
          <h3>Density Rate</h3>
          <Line
            data={{
              labels: metrics.timestamps,
              datasets: [{
                label: 'Density',
                data: metrics.density,
                borderColor: '#ff9f40',
                pointRadius: 0
              }]
            }}
            options={{ 
              ...chartOptions,
              scales: {
                ...chartOptions.scales,
                y: {
                  beginAtZero: true,
                  max: 1
                }
              }
            }}
          />
        </div>

        <div className="chart-wrapper">
          <h3>Movement Velocity</h3>
          <Line
            data={{
              labels: metrics.timestamps,
              datasets: [{
                label: 'Velocity (px/frame)',
                data: metrics.velocity,
                borderColor: '#ff6384',
                pointRadius: 0
              }]
            }}
            options={chartOptions}
          />
        </div>
      </div>
    </div>
  </div>
);
}
export default App;