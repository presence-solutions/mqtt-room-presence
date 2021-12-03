import type { AxiosResponse } from 'axios';
import axios from './axios';

export type RoomResponseModel = {
  id: number,
  name: string,
  created_at: string,
  updated_at: string
};

export function getRooms(): Promise<AxiosResponse<RoomResponseModel[]>> {
  return axios.get('/room');
}
