interface WithStringId {
  id: string
}

interface WithOptionalStringIdAndUuid {
  id?: string | null | undefined,
  uuid: string
}

export function sortArrayByStringId<T extends WithStringId>(arr: T[], asc = true): T[] {
  const options: Intl.CollatorOptions = { numeric: true };

  return arr.sort(
    (item1, item2) => asc
      ? item1.id.localeCompare(item2.id, [], options)
      : item2.id.localeCompare(item1.id, [], options)
  );
}

export function sortArrayByIdAndUuid<T extends WithOptionalStringIdAndUuid>(
  arr: T[],
  asc = true
): T[] {
  const options: Intl.CollatorOptions = { numeric: true };

  return arr.sort(
    (item1, item2) => {
      const item1_id = item1.id || undefined;
      const item2_id = item2.id || undefined;

      if (item1_id && !item2_id) {
        return -1;
      }

      if (!item1_id && item2_id) {
        return 1;
      }

      if (item1_id === item2_id) {
        return asc
          ? item1.uuid.localeCompare(item2.uuid)
          : item2.uuid.localeCompare(item1.uuid);
      }

      return asc
        ? item1_id!.localeCompare(item2_id!, [], options)
        : item2_id!.localeCompare(item1_id!, [], options);
    }
  );
}
