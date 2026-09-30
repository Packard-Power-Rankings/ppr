export const formatDisplayName = (value = '') =>
  value.replace(/[_-]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())

export const formatDatasetName = ({ sport, gender, level }) =>
  [level, gender, sport].map(formatDisplayName).join(' ')
