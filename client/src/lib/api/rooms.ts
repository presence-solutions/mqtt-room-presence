import type { AxiosResponse } from 'axios';
import axios from './axios';

export type RoomResponseModel = {
  id: number,
  name: string,
  created_at: string,
  updated_at: string
};

let rooms = [
  {
    id: 1,
    created_at: '2021-03-19T06:39:26.014140+00:00',
    updated_at: '2021-03-19T06:39:26.014168+00:00',
    name: 'Office'
  },
  {
    id: 2,
    created_at: '2021-03-19T06:39:26.017419+00:00',
    updated_at: '2021-03-19T06:39:26.017435+00:00',
    name: 'Kitchen'
  },
  {
    id: 3,
    created_at: '2021-03-19T06:39:26.020232+00:00',
    updated_at: '2021-03-19T06:39:26.020245+00:00',
    name: 'Lobby'
  }
];


export function getRooms(): Promise<RoomResponseModel[]> {
  return Promise.resolve(rooms);
  // return axios.get('/room');
}

export function addRoom({ name }: { name: string }): Promise<RoomResponseModel> {
  const newRoom = {
    id: rooms[rooms.length - 1].id + 1,
    name,
    created_at: '2021-03-19T06:39:26.030703+00:00',
    updated_at: '2021-03-19T06:39:26.030715+00:00'
  };

  rooms.push(newRoom);

  return Promise.resolve(newRoom);
}

export function editRoom({ id, name }: { id: number, name: string }): Promise<RoomResponseModel> {
  const roomIndex = rooms.findIndex(r => r.id === id);

  if (roomIndex >= 0) {
    rooms[roomIndex].name = name;

    return Promise.resolve(rooms[roomIndex]);
  };

  return Promise.reject();
}

export function deleteRoom({ id }: { id: number }): Promise<Array<RoomResponseModel>> {
  rooms = rooms.filter(r => r.id !== id);

  return Promise.resolve(rooms);
}
