export function formatUtc(value?: string): string {
  if (!value) return "Unavailable";
  const parts =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$/.exec(
      value,
    );
  if (!parts) return "Unavailable";
  const [year, month, day, hour, minute, second] = parts
    .slice(1, 7)
    .map(Number);
  const calendar = new Date(Date.UTC(year, month - 1, day));
  if (
    calendar.getUTCFullYear() !== year ||
    calendar.getUTCMonth() !== month - 1 ||
    calendar.getUTCDate() !== day ||
    hour > 23 ||
    minute > 59 ||
    second > 59
  )
    return "Unavailable";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "Unavailable";
  // Offset conversion preserves the fractional second; Date alone truncates it.
  const iso = date.toISOString();
  const fraction = parts[7] ?? "";
  const precise =
    fraction.length > 3 ? iso.replace(/\.\d{3}Z$/, `.${fraction}Z`) : iso;
  return `${precise} (UTC)`;
}
