import React, { useCallback, useEffect, useState } from 'react'
import {
  CAlert,
  CButton,
  CCol,
  CContainer,
  CForm,
  CFormInput,
  CFormLabel,
  CRow,
  CSpinner,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilSave, cilSearch } from '@coreui/icons'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation } from 'react-router-dom'
import Select from 'react-select'
import api from 'src/api'
import { formatDatasetName } from 'src/utils/displayNames'

const UpdateGame = () => {
  const dispatch = useDispatch()
  const location = useLocation()
  const flaggedIssue = location.state?.flaggedIssue
  const sport = useSelector((state) => state.sport)
  const gender = useSelector((state) => state.gender)
  const level = useSelector((state) => state.level)
  const [teamsOptions, setTeamsOptions] = useState([])
  const [teamOne, setTeamOne] = useState(null)
  const [teamTwo, setTeamTwo] = useState(null)
  const [gameOptions, setGameOptions] = useState([])
  const [selectedGame, setSelectedGame] = useState(null)
  const [homeScore, setHomeScore] = useState('')
  const [awayScore, setAwayScore] = useState('')
  const [loadingTeams, setLoadingTeams] = useState(true)
  const [loadingGames, setLoadingGames] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [loadError, setLoadError] = useState(false)
  const [gamesLoaded, setGamesLoaded] = useState(false)
  const [resultMessage, setResultMessage] = useState('')
  const [resultColor, setResultColor] = useState('info')
  const datasetName = formatDatasetName({ sport, gender, level })
  const game = selectedGame?.game
  const scoresValid =
    homeScore !== '' &&
    awayScore !== '' &&
    Number.isInteger(Number(homeScore)) &&
    Number.isInteger(Number(awayScore)) &&
    Number(homeScore) >= 0 &&
    Number(awayScore) >= 0

  const fetchGames = useCallback(async (firstTeam, secondTeam, targetGameId = null) => {
    setLoadingGames(true)
    setGamesLoaded(false)
    setGameOptions([])
    setSelectedGame(null)
    setHomeScore('')
    setAwayScore('')
    setResultMessage('')

    try {
      const response = await api.get(`/season-dates/${firstTeam.value}/${secondTeam.value}`, {
        params: {
          sport_type: sport,
          gender,
          level,
        },
      })
      const games = Array.isArray(response.data) ? response.data : []
      const options = games.map((item) => ({
        value: item.game_id,
        label: `${item.game_date}: ${item.home_team_name} ${item.home_score} - ${item.away_score} ${item.away_team_name}`,
        game: item,
      }))
      setGameOptions(options)
      setGamesLoaded(true)

      if (targetGameId !== null) {
        const targetGame = options.find((option) => String(option.value) === String(targetGameId))
        if (targetGame) {
          setSelectedGame(targetGame)
          setHomeScore(String(targetGame.game.home_score))
          setAwayScore(String(targetGame.game.away_score))
        } else {
          setResultColor('danger')
          setResultMessage('The flagged game could not be found between the selected teams.')
        }
      }
    } catch (error) {
      console.error('Failed to retrieve games', error)
      setResultColor('danger')
      setResultMessage(error.response?.data?.detail || 'Failed to load games')
    } finally {
      setLoadingGames(false)
    }
  }, [sport, gender, level])

  useEffect(() => {
    let isCurrentRequest = true

    const fetchTeams = async () => {
      setLoadingTeams(true)
      setLoadError(false)
      setTeamsOptions([])
      setTeamOne(null)
      setTeamTwo(null)
      setGameOptions([])
      setSelectedGame(null)
      setGamesLoaded(false)
      setResultMessage('')

      if (flaggedIssue && (
        sport !== flaggedIssue.sport_type ||
        gender !== flaggedIssue.gender ||
        level !== flaggedIssue.level
      )) {
        dispatch({
          type: 'updateAdminState',
          payload: {
            sport: flaggedIssue.sport_type,
            gender: flaggedIssue.gender,
            level: flaggedIssue.level,
          },
        })
        return
      }

      try {
        const response = await api.get('/teams-ids/', {
          params: {
            sport_type: sport,
            gender,
            level,
          },
        })

        if (!isCurrentRequest) return

        if (response.status === 204 || response.data?.status === 204) return
        const teams = response.data?.data?.teams
        if (!Array.isArray(teams)) {
          throw new Error('Teams response did not contain a teams array')
        }
        const options = teams.map((team) => ({
          value: team.team_id,
          label: team.team_name,
        }))
        setTeamsOptions(options)

        if (flaggedIssue) {
          const selectedTeamOne = options.find(
            (team) => String(team.value) === String(flaggedIssue.team1_id),
          )
          const selectedTeamTwo = options.find(
            (team) => String(team.value) === String(flaggedIssue.team2_id),
          )
          if (selectedTeamOne && selectedTeamTwo) {
            setTeamOne(selectedTeamOne)
            setTeamTwo(selectedTeamTwo)
            await fetchGames(selectedTeamOne, selectedTeamTwo, flaggedIssue.game_id)
          } else {
            setResultColor('danger')
            setResultMessage('The flagged game teams could not be found in this dataset.')
          }
        }
      } catch (error) {
        if (!isCurrentRequest) return
        console.error('Failed to retrieve teams for game update', error)
        setLoadError(true)
      } finally {
        if (isCurrentRequest) setLoadingTeams(false)
      }
    }

    fetchTeams()
    return () => {
      isCurrentRequest = false
    }
  }, [dispatch, fetchGames, flaggedIssue, sport, gender, level])

  const resetGameSelection = () => {
    setGameOptions([])
    setSelectedGame(null)
    setHomeScore('')
    setAwayScore('')
    setGamesLoaded(false)
    setResultMessage('')
  }

  const handleFindGames = () => {
    if (!teamOne || !teamTwo) return
    fetchGames(teamOne, teamTwo)
  }

  const handleGameChange = (option) => {
    setSelectedGame(option)
    setHomeScore(option ? String(option.game.home_score) : '')
    setAwayScore(option ? String(option.game.away_score) : '')
    setResultMessage('')
  }

  const handleUpdateGame = async (event) => {
    event.preventDefault()
    if (!game || !scoresValid) return

    setUpdating(true)
    setResultMessage('')
    try {
      const response = await api.put('/update-game/', {}, {
        params: {
          date: game.game_date,
          game_id: game.game_id,
          home_team: game.home_team_name,
          away_team: game.away_team_name,
          home_score: Number(homeScore),
          away_score: Number(awayScore),
          sport_type: sport,
          gender,
          level,
        },
      })

      if (response.data?.status !== 200) {
        throw new Error(response.data?.message || 'The game could not be updated')
      }

      setResultColor('success')
      setResultMessage(response.data?.message || 'Game scores were updated')
      const updatedGame = {
        ...game,
        home_score: Number(homeScore),
        away_score: Number(awayScore),
      }
      const updatedOption = {
        ...selectedGame,
        label: `${game.game_date}: ${game.home_team_name} ${homeScore} - ${awayScore} ${game.away_team_name}`,
        game: updatedGame,
      }
      setSelectedGame(updatedOption)
      setGameOptions((options) =>
        options.map((option) => (option.value === updatedOption.value ? updatedOption : option)),
      )
    } catch (error) {
      console.error('Failed to update game', error)
      setResultColor('danger')
      setResultMessage(error.response?.data?.detail || 'The game could not be updated')
    } finally {
      setUpdating(false)
    }
  }

  return (
    <CContainer className="mt-4">
      <CRow className="mb-3">
        <CCol>
          <h4>Update Game</h4>
        </CCol>
      </CRow>

      {loadError && <CAlert color="danger">Failed to Load {datasetName} Teams</CAlert>}
      {!loadingTeams && !loadError && teamsOptions.length === 0 && (
        <CAlert color="info">No {datasetName} Teams Found</CAlert>
      )}
      {resultMessage && <CAlert color={resultColor}>{resultMessage}</CAlert>}

      <CRow className="g-3 align-items-end mb-4">
        <CCol md={5}>
          <CFormLabel htmlFor="update-game-team-one">First Team</CFormLabel>
          <Select
            aria-label="First Team"
            classNamePrefix="react-select"
            inputId="update-game-team-one"
            isClearable
            isDisabled={loadingTeams || loadError}
            isLoading={loadingTeams}
            isSearchable
            onChange={(option) => {
              setTeamOne(option)
              setTeamTwo(null)
              resetGameSelection()
            }}
            options={teamsOptions}
            placeholder="Select Team"
            value={teamOne}
          />
        </CCol>
        <CCol md={5}>
          <CFormLabel htmlFor="update-game-team-two">Second Team</CFormLabel>
          <Select
            aria-label="Second Team"
            classNamePrefix="react-select"
            inputId="update-game-team-two"
            isClearable
            isDisabled={!teamOne || loadingTeams || loadError}
            isSearchable
            onChange={(option) => {
              setTeamTwo(option)
              resetGameSelection()
            }}
            options={teamsOptions.filter((team) => team.value !== teamOne?.value)}
            placeholder="Select Team"
            value={teamTwo}
          />
        </CCol>
        <CCol md={2}>
          <CButton
            color="primary"
            disabled={!teamOne || !teamTwo || loadingGames}
            onClick={handleFindGames}
            type="button"
          >
            {loadingGames ? (
              <CSpinner className="me-2" size="sm" />
            ) : (
              <CIcon icon={cilSearch} className="me-2" />
            )}
            Find Games
          </CButton>
        </CCol>
      </CRow>

      {gamesLoaded && gameOptions.length === 0 && (
        <CAlert color="info">No Games Found Between the Selected Teams</CAlert>
      )}

      {gameOptions.length > 0 && (
        <CForm onSubmit={handleUpdateGame}>
          <CRow className="g-3 align-items-end">
            <CCol xs={12}>
              <CFormLabel htmlFor="update-game-selection">Game</CFormLabel>
              <Select
                aria-label="Game"
                classNamePrefix="react-select"
                inputId="update-game-selection"
                isClearable
                isSearchable
                onChange={handleGameChange}
                options={gameOptions}
                placeholder="Select Game"
                value={selectedGame}
              />
            </CCol>
            <CCol md={5}>
              <CFormLabel htmlFor="update-home-score">
                {game?.home_team_name || 'Home Team'} Score
              </CFormLabel>
              <CFormInput
                disabled={!game}
                id="update-home-score"
                min={0}
                onChange={(event) => setHomeScore(event.target.value)}
                step={1}
                type="number"
                value={homeScore}
              />
            </CCol>
            <CCol md={5}>
              <CFormLabel htmlFor="update-away-score">
                {game?.away_team_name || 'Away Team'} Score
              </CFormLabel>
              <CFormInput
                disabled={!game}
                id="update-away-score"
                min={0}
                onChange={(event) => setAwayScore(event.target.value)}
                step={1}
                type="number"
                value={awayScore}
              />
            </CCol>
            <CCol md={2}>
              <CButton
                color="primary"
                disabled={!game || !scoresValid || updating}
                type="submit"
              >
                {updating ? (
                  <CSpinner className="me-2" size="sm" />
                ) : (
                  <CIcon icon={cilSave} className="me-2" />
                )}
                Update Game
              </CButton>
            </CCol>
          </CRow>
        </CForm>
      )}
    </CContainer>
  )
}

export default UpdateGame
