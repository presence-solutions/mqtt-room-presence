import gql from 'graphql-tag';
import * as Urql from 'urql';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: string;
  String: string;
  Boolean: boolean;
  Int: number;
  Float: number;
  Datetime: any;
};

export type Device = {
  __typename?: 'Device';
  createdAt: Scalars['Datetime'];
  displayName?: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  name?: Maybe<Scalars['String']>;
  predictionModel?: Maybe<PredictionModel>;
  updatedAt: Scalars['Datetime'];
  useNameAsId: Scalars['Boolean'];
  usedByModels?: Maybe<Array<PredictionModel>>;
  uuid?: Maybe<Scalars['String']>;
};

export type DeviceCreateResult = {
  __typename?: 'DeviceCreateResult';
  device?: Maybe<Device>;
  error?: Maybe<ExecutionError>;
};

export type DeviceSignal = {
  __typename?: 'DeviceSignal';
  createdAt: Scalars['Datetime'];
  device: Device;
  id?: Maybe<Scalars['ID']>;
  learningSession?: Maybe<LearningSession>;
  room?: Maybe<Room>;
  rssi: Scalars['Int'];
  scanner: Scanner;
  updatedAt: Scalars['Datetime'];
};

export type DeviceUpdateResult = {
  __typename?: 'DeviceUpdateResult';
  device?: Maybe<Device>;
  error?: Maybe<ExecutionError>;
};

export type ExecutionError = {
  __typename?: 'ExecutionError';
  code?: Maybe<Scalars['String']>;
  message?: Maybe<Scalars['String']>;
};

export type LearningSession = {
  __typename?: 'LearningSession';
  id: Scalars['ID'];
};

export type ModelTrainingProgress = {
  __typename?: 'ModelTrainingProgress';
  device: Device;
  isError?: Maybe<Scalars['Boolean']>;
  isFinal?: Maybe<Scalars['Boolean']>;
  message: Scalars['String'];
  predictionModel?: Maybe<PredictionModel>;
  statusCode: Scalars['String'];
};

export type ModelTrainingProgressResult = {
  __typename?: 'ModelTrainingProgressResult';
  error?: Maybe<ExecutionError>;
  progress?: Maybe<ModelTrainingProgress>;
};

export type Mutation = {
  __typename?: 'Mutation';
  addDevice: DeviceCreateResult;
  addRoom: RoomCreateResult;
  addScanner: ScannerCreateResult;
  removeDevice?: Maybe<Device>;
  removePredictionModel?: Maybe<PredictionModel>;
  removeRoom?: Maybe<Room>;
  removeScanner?: Maybe<Scanner>;
  startModelTraining: ModelTrainingProgressResult;
  startSignalsRecording: StartSignalsRecordingResult;
  stopSignalsRecording?: Maybe<StopSignalsRecordingResult>;
  updateDevice: DeviceUpdateResult;
  updateRoom: RoomUpdateResult;
  updateScanner: ScannerUpdateResult;
};


export type MutationAddDeviceArgs = {
  input: NewDeviceInput;
};


export type MutationAddRoomArgs = {
  input: NewRoomInput;
};


export type MutationAddScannerArgs = {
  input: NewScannerInput;
};


export type MutationRemoveDeviceArgs = {
  id: Scalars['ID'];
};


export type MutationRemovePredictionModelArgs = {
  id: Scalars['ID'];
};


export type MutationRemoveRoomArgs = {
  id: Scalars['ID'];
};


export type MutationRemoveScannerArgs = {
  id: Scalars['ID'];
};


export type MutationStartModelTrainingArgs = {
  device: Scalars['ID'];
};


export type MutationStartSignalsRecordingArgs = {
  device: Scalars['ID'];
  room: Scalars['ID'];
};


export type MutationUpdateDeviceArgs = {
  input: UpdateDeviceInput;
};


export type MutationUpdateRoomArgs = {
  input: UpdateRoomInput;
};


export type MutationUpdateScannerArgs = {
  input: UpdateScannerInput;
};

export type NewDeviceInput = {
  displayName?: InputMaybe<Scalars['String']>;
  name: Scalars['String'];
  predictionModel?: InputMaybe<Scalars['ID']>;
  useNameAsId?: InputMaybe<Scalars['Boolean']>;
  uuid: Scalars['String'];
};

export type NewRoomInput = {
  name: Scalars['String'];
  scanners?: InputMaybe<Array<Scalars['ID']>>;
};

export type NewScannerInput = {
  displayName?: InputMaybe<Scalars['String']>;
  usedInRooms?: InputMaybe<Array<Scalars['ID']>>;
  uuid: Scalars['String'];
};

export type PredictionModel = {
  __typename?: 'PredictionModel';
  accuracy?: Maybe<Scalars['Float']>;
  createdAt: Scalars['Datetime'];
  devices?: Maybe<Array<Device>>;
  displayName?: Maybe<Scalars['String']>;
  id: Scalars['ID'];
  inputsHash: Scalars['String'];
  updatedAt: Scalars['Datetime'];
  usedByDevices?: Maybe<Array<Device>>;
};

export type Query = {
  __typename?: 'Query';
  allDevices: Array<Device>;
  allPredictionModels: Array<PredictionModel>;
  allRooms: Array<Room>;
  allScanners: Array<Scanner>;
};

export type Room = {
  __typename?: 'Room';
  createdAt: Scalars['Datetime'];
  id: Scalars['ID'];
  name?: Maybe<Scalars['String']>;
  scanners?: Maybe<Array<Scanner>>;
  updatedAt: Scalars['Datetime'];
};

export type RoomCreateResult = {
  __typename?: 'RoomCreateResult';
  error?: Maybe<ExecutionError>;
  room?: Maybe<Room>;
};

export type RoomState = {
  __typename?: 'RoomState';
  devices?: Maybe<Array<Device>>;
  room: Room;
  state: Scalars['Boolean'];
};

export type RoomUpdateResult = {
  __typename?: 'RoomUpdateResult';
  error?: Maybe<ExecutionError>;
  room?: Maybe<Room>;
};

export type Scanner = {
  __typename?: 'Scanner';
  createdAt?: Maybe<Scalars['Datetime']>;
  displayName?: Maybe<Scalars['String']>;
  id?: Maybe<Scalars['ID']>;
  unknown?: Maybe<Scalars['Boolean']>;
  updatedAt?: Maybe<Scalars['Datetime']>;
  usedInRooms?: Maybe<Array<Room>>;
  uuid: Scalars['String'];
};

export type ScannerCreateResult = {
  __typename?: 'ScannerCreateResult';
  error?: Maybe<ExecutionError>;
  scanner?: Maybe<Scanner>;
};

export type ScannerUpdateResult = {
  __typename?: 'ScannerUpdateResult';
  error?: Maybe<ExecutionError>;
  scanner?: Maybe<Scanner>;
};

export type StartSignalsRecordingResult = {
  __typename?: 'StartSignalsRecordingResult';
  error?: Maybe<ExecutionError>;
};

export type StopSignalsRecordingResult = {
  __typename?: 'StopSignalsRecordingResult';
  error?: Maybe<ExecutionError>;
  recording?: Maybe<LearningSession>;
};

export type Subscription = {
  __typename?: 'Subscription';
  deviceSignal: DeviceSignal;
  learntSignal: DeviceSignal;
  modelTrainingProgress: ModelTrainingProgressResult;
  roomState: RoomState;
};


export type SubscriptionDeviceSignalArgs = {
  device?: InputMaybe<Scalars['ID']>;
  scanner?: InputMaybe<Scalars['ID']>;
};


export type SubscriptionModelTrainingProgressArgs = {
  device: Scalars['ID'];
};


export type SubscriptionRoomStateArgs = {
  room?: InputMaybe<Scalars['ID']>;
};

export type UpdateDeviceInput = {
  displayName?: InputMaybe<Scalars['String']>;
  id: Scalars['ID'];
  name: Scalars['String'];
  predictionModel?: InputMaybe<Scalars['ID']>;
  useNameAsId?: InputMaybe<Scalars['Boolean']>;
  uuid: Scalars['String'];
};

export type UpdateRoomInput = {
  id: Scalars['ID'];
  name: Scalars['String'];
  scanners?: InputMaybe<Array<Scalars['ID']>>;
};

export type UpdateScannerInput = {
  displayName?: InputMaybe<Scalars['String']>;
  id: Scalars['ID'];
  usedInRooms?: InputMaybe<Array<Scalars['ID']>>;
  uuid: Scalars['String'];
};

export type GetAllDevicesQueryVariables = Exact<{ [key: string]: never; }>;


export type GetAllDevicesQuery = { __typename?: 'Query', allDevices: Array<{ __typename?: 'Device', id: string, uuid?: string | null | undefined, name?: string | null | undefined }> };

export type AddDeviceMutationVariables = Exact<{
  newDevice: NewDeviceInput;
}>;


export type AddDeviceMutation = { __typename?: 'Mutation', addDevice: { __typename?: 'DeviceCreateResult', device?: { __typename?: 'Device', id: string, name?: string | null | undefined, uuid?: string | null | undefined } | null | undefined } };

export type UpdateDeviceMutationVariables = Exact<{
  device: UpdateDeviceInput;
}>;


export type UpdateDeviceMutation = { __typename?: 'Mutation', updateDevice: { __typename?: 'DeviceUpdateResult', device?: { __typename?: 'Device', id: string, name?: string | null | undefined, uuid?: string | null | undefined } | null | undefined } };

export type RemoveDeviceMutationVariables = Exact<{
  deviceId: Scalars['ID'];
}>;


export type RemoveDeviceMutation = { __typename?: 'Mutation', removeDevice?: { __typename?: 'Device', id: string } | null | undefined };

export type GetAllRoomsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetAllRoomsQuery = { __typename?: 'Query', allRooms: Array<{ __typename?: 'Room', id: string, name?: string | null | undefined, scanners?: Array<{ __typename?: 'Scanner', id?: string | null | undefined, uuid: string }> | null | undefined }> };

export type AddRoomMutationVariables = Exact<{
  newRoom: NewRoomInput;
}>;


export type AddRoomMutation = { __typename?: 'Mutation', addRoom: { __typename?: 'RoomCreateResult', room?: { __typename?: 'Room', id: string, name?: string | null | undefined, scanners?: Array<{ __typename?: 'Scanner', id?: string | null | undefined, uuid: string }> | null | undefined } | null | undefined } };

export type UpdateRoomMutationVariables = Exact<{
  room: UpdateRoomInput;
}>;


export type UpdateRoomMutation = { __typename?: 'Mutation', updateRoom: { __typename?: 'RoomUpdateResult', room?: { __typename?: 'Room', id: string, name?: string | null | undefined, scanners?: Array<{ __typename?: 'Scanner', id?: string | null | undefined, uuid: string }> | null | undefined } | null | undefined } };

export type RemoveRoomMutationVariables = Exact<{
  roomId: Scalars['ID'];
}>;


export type RemoveRoomMutation = { __typename?: 'Mutation', removeRoom?: { __typename?: 'Room', id: string } | null | undefined };

export type GetAllScannersQueryVariables = Exact<{ [key: string]: never; }>;


export type GetAllScannersQuery = { __typename?: 'Query', allScanners: Array<{ __typename?: 'Scanner', id?: string | null | undefined, uuid: string, usedInRooms?: Array<{ __typename?: 'Room', id: string, name?: string | null | undefined }> | null | undefined }> };

export type AddScannerMutationVariables = Exact<{
  newScanner: NewScannerInput;
}>;


export type AddScannerMutation = { __typename?: 'Mutation', addScanner: { __typename?: 'ScannerCreateResult', scanner?: { __typename?: 'Scanner', id?: string | null | undefined, uuid: string } | null | undefined } };

export type UpdateScannerMutationVariables = Exact<{
  scanner: UpdateScannerInput;
}>;


export type UpdateScannerMutation = { __typename?: 'Mutation', updateScanner: { __typename?: 'ScannerUpdateResult', scanner?: { __typename?: 'Scanner', id?: string | null | undefined, uuid: string } | null | undefined } };

export type RemoveScannerMutationVariables = Exact<{
  scannerId: Scalars['ID'];
}>;


export type RemoveScannerMutation = { __typename?: 'Mutation', removeScanner?: { __typename?: 'Scanner', id?: string | null | undefined } | null | undefined };


export const GetAllDevicesDocument = gql`
    query GetAllDevices {
  allDevices {
    id
    uuid
    name
  }
}
    `;

export function useGetAllDevicesQuery(options: Omit<Urql.UseQueryArgs<GetAllDevicesQueryVariables>, 'query'> = {}) {
  return Urql.useQuery<GetAllDevicesQuery>({ query: GetAllDevicesDocument, ...options });
};
export const AddDeviceDocument = gql`
    mutation AddDevice($newDevice: NewDeviceInput!) {
  addDevice(input: $newDevice) {
    device {
      id
      name
      uuid
    }
  }
}
    `;

export function useAddDeviceMutation() {
  return Urql.useMutation<AddDeviceMutation, AddDeviceMutationVariables>(AddDeviceDocument);
};
export const UpdateDeviceDocument = gql`
    mutation UpdateDevice($device: UpdateDeviceInput!) {
  updateDevice(input: $device) {
    device {
      id
      name
      uuid
    }
  }
}
    `;

export function useUpdateDeviceMutation() {
  return Urql.useMutation<UpdateDeviceMutation, UpdateDeviceMutationVariables>(UpdateDeviceDocument);
};
export const RemoveDeviceDocument = gql`
    mutation RemoveDevice($deviceId: ID!) {
  removeDevice(id: $deviceId) {
    id
  }
}
    `;

export function useRemoveDeviceMutation() {
  return Urql.useMutation<RemoveDeviceMutation, RemoveDeviceMutationVariables>(RemoveDeviceDocument);
};
export const GetAllRoomsDocument = gql`
    query GetAllRooms {
  allRooms {
    id
    name
    scanners {
      id
      uuid
    }
  }
}
    `;

export function useGetAllRoomsQuery(options: Omit<Urql.UseQueryArgs<GetAllRoomsQueryVariables>, 'query'> = {}) {
  return Urql.useQuery<GetAllRoomsQuery>({ query: GetAllRoomsDocument, ...options });
};
export const AddRoomDocument = gql`
    mutation AddRoom($newRoom: NewRoomInput!) {
  addRoom(input: $newRoom) {
    room {
      id
      name
      scanners {
        id
        uuid
      }
    }
  }
}
    `;

export function useAddRoomMutation() {
  return Urql.useMutation<AddRoomMutation, AddRoomMutationVariables>(AddRoomDocument);
};
export const UpdateRoomDocument = gql`
    mutation UpdateRoom($room: UpdateRoomInput!) {
  updateRoom(input: $room) {
    room {
      id
      name
      scanners {
        id
        uuid
      }
    }
  }
}
    `;

export function useUpdateRoomMutation() {
  return Urql.useMutation<UpdateRoomMutation, UpdateRoomMutationVariables>(UpdateRoomDocument);
};
export const RemoveRoomDocument = gql`
    mutation RemoveRoom($roomId: ID!) {
  removeRoom(id: $roomId) {
    id
  }
}
    `;

export function useRemoveRoomMutation() {
  return Urql.useMutation<RemoveRoomMutation, RemoveRoomMutationVariables>(RemoveRoomDocument);
};
export const GetAllScannersDocument = gql`
    query GetAllScanners {
  allScanners {
    id
    uuid
    usedInRooms {
      id
      name
    }
  }
}
    `;

export function useGetAllScannersQuery(options: Omit<Urql.UseQueryArgs<GetAllScannersQueryVariables>, 'query'> = {}) {
  return Urql.useQuery<GetAllScannersQuery>({ query: GetAllScannersDocument, ...options });
};
export const AddScannerDocument = gql`
    mutation AddScanner($newScanner: NewScannerInput!) {
  addScanner(input: $newScanner) {
    scanner {
      id
      uuid
    }
  }
}
    `;

export function useAddScannerMutation() {
  return Urql.useMutation<AddScannerMutation, AddScannerMutationVariables>(AddScannerDocument);
};
export const UpdateScannerDocument = gql`
    mutation UpdateScanner($scanner: UpdateScannerInput!) {
  updateScanner(input: $scanner) {
    scanner {
      id
      uuid
    }
  }
}
    `;

export function useUpdateScannerMutation() {
  return Urql.useMutation<UpdateScannerMutation, UpdateScannerMutationVariables>(UpdateScannerDocument);
};
export const RemoveScannerDocument = gql`
    mutation RemoveScanner($scannerId: ID!) {
  removeScanner(id: $scannerId) {
    id
  }
}
    `;

export function useRemoveScannerMutation() {
  return Urql.useMutation<RemoveScannerMutation, RemoveScannerMutationVariables>(RemoveScannerDocument);
};