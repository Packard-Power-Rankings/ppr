export const formatDisplayName = (value = '') =>
  value.replace(/[_-]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())

export const formatDatasetName = ({ sport, sport_type: sportType, gender, level }) =>
  [level, gender, sport || sportType].map(formatDisplayName).filter(Boolean).join(' ')
