import { sortArrayByStringId, sortArrayByIdAndUuid } from './sortArray';

describe('test sortArrayByStringId', () => {
  const initializeArray = () => [
    { id: '3' },
    { id: '2' },
    { id: '1' },
    { id: '12' },
    { id: '10' },
    { id: '142' },
    { id: '23' }
  ];

  test('ascending', () => {
    const arr = initializeArray();
    const expectedValue = [
      { id: '1' },
      { id: '2' },
      { id: '3' },
      { id: '10' },
      { id: '12' },
      { id: '23' },
      { id: '142' }
    ];
    expect(sortArrayByStringId(arr)).toEqual(expectedValue);
  });

  test('descending', () => {
    const arr = initializeArray();
    const expectedValue = [
      { id: '142' },
      { id: '23' },
      { id: '12' },
      { id: '10' },
      { id: '3' },
      { id: '2' },
      { id: '1' }
    ];
    expect(sortArrayByStringId(arr, false)).toEqual(expectedValue);
  });
});

describe('test sortArrayByIdAndUuid', () => {
  const initializeArray = () => [
    { id: '3', uuid: 'abc' },
    { id: '2', uuid: 'asd' },
    { id: '1', uuid: 'qwe' },
    { id: '12', uuid: 'zxc' },
    { id: '10', uuid: 'cxz' },
    { uuid: 'aaa' },
    { uuid: 'zzz' },
    { id: '142', uuid: '123' },
    { id: '23', uuid: '456' },
    { id: null, uuid: '789' },
    { id: null, uuid: '987' }
  ];

  test('ascending', () => {
    const arr = initializeArray();
    const expectedValue = [
      { id: '1', uuid: 'qwe' },
      { id: '2', uuid: 'asd' },
      { id: '3', uuid: 'abc' },
      { id: '10', uuid: 'cxz' },
      { id: '12', uuid: 'zxc' },
      { id: '23', uuid: '456' },
      { id: '142', uuid: '123' },
      { id: null, uuid: '789' },
      { id: null, uuid: '987' },
      { uuid: 'aaa' },
      { uuid: 'zzz' }
    ];

    expect(sortArrayByIdAndUuid(arr)).toEqual(expectedValue);
  });

  test('descending', () => {
    const arr = initializeArray();
    const expectedValue = [
      { id: '142', uuid: '123' },
      { id: '23', uuid: '456' },
      { id: '12', uuid: 'zxc' },
      { id: '10', uuid: 'cxz' },
      { id: '3', uuid: 'abc' },
      { id: '2', uuid: 'asd' },
      { id: '1', uuid: 'qwe' },
      { uuid: 'zzz' },
      { uuid: 'aaa' },
      { id: null, uuid: '987' },
      { id: null, uuid: '789' }
    ];

    expect(sortArrayByIdAndUuid(arr, false)).toEqual(expectedValue);
  });
});
