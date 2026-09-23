import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitVerification = async (data) => {
  const response = await client.post('/verify', data);
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await client.get(`/jobs/${jobId}`);
  return response.data;
};

export const getReport = async (reportId) => {
  const response = await client.get(`/reports/${reportId}`);
  return response.data;
};

export const getCertificate = async (certId) => {
  const response = await client.get(`/certificates/${certId}`);
  return response.data;
};

export const submitReview = async (certId, data) => {
  const response = await client.post(`/review/${certId}`, data);
  return response.data;
};

export const getLedger = async (params) => {
  const response = await client.get('/ledger', { params });
  return response.data;
};

export const downloadCertificatePdf = async (certId) => {
  const response = await client.get(`/certificates/${certId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

export const getPublicKey = async () => {
  const response = await client.get('/public-key');
  return response.data;
};

export default client;
