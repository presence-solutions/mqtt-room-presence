import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://192.168.56.102:5000/api/'
});

export default axiosInstance;
