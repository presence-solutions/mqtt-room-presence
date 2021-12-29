interface WithStringId {
  id: string
}

export function sortArrayByStringId<T extends WithStringId>(arr: T[], asc = true): T[] {
  const options: Intl.CollatorOptions = { numeric: true };

  return arr.sort(
    (item1, item2) => asc
      ? item1.id.localeCompare(item2.id, [], options)
      : item2.id.localeCompare(item1.id, [], options)
  );
}
