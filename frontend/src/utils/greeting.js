// Time-of-day greeting, e.g. "Good morning" / "Good afternoon" / "Good evening".
export function timeOfDayGreeting(date = new Date()) {
  const hour = date.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}
