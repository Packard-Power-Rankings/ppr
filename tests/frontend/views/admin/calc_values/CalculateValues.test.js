import React from 'react'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import api from 'src/api'
import CalculateValues from 'src/views/admin/calc_values/CalculateValues'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}))

jest.mock('react-redux', () => ({
  useSelector: (selector) => selector({
    sport: 'basketball',
    gender: 'womens',
    level: 'college',
  }),
}))

beforeEach(() => {
  api.get.mockReset()
  api.post.mockReset()
})

test('loads persisted algorithm history when Ranking opens', async () => {
  api.get.mockResolvedValue({
    data: {
      algorithm: [{
        task_id: 'previous-run',
        queued_at: '2026-10-01T12:00:00Z',
        started_at: '2026-10-01T10:00:00Z',
        finished_at: '2026-10-01T11:05:06Z',
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
        iterations: 4,
        status: 'complete',
      }, {
        task_id: 'other-dataset-run',
        queued_at: '2026-10-01T11:00:00Z',
        sport_type: 'football',
        gender: 'mens',
        level: 'high_school',
        iterations: 2,
        status: 'complete',
      }],
      z_scores: [],
    },
  })

  render(<CalculateValues />)

  expect(screen.getByRole('heading', { name: /Ranking$/ })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Calculate z Scores' })).not.toBeInTheDocument()
  expect(await screen.findByText('College Womens Basketball')).toBeInTheDocument()
  expect(screen.queryByText('High School Mens Football')).not.toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Elapsed Time' })).toBeInTheDocument()
  expect(screen.getByText('1H 5M 6S')).toBeInTheDocument()
  expect(screen.getByRole('img', { name: 'Successfully completed' }).closest('.text-success'))
    .toBeInTheDocument()
  expect(screen.getByText('4')).toBeInTheDocument()
  expect(screen.getByText('Complete')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/execution-history/')
})

test('shows persisted failure details from the failed status info icon', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({
    data: {
      algorithm: [{
        task_id: 'failed-run',
        queued_at: '2026-10-01T12:00:00Z',
        started_at: '2026-10-01T12:00:01Z',
        finished_at: '2026-10-01T12:00:02Z',
        iterations: 2,
        status: 'failed',
        error: {
          type: 'HTTPException',
          message: '404: No games were found for the selected dataset',
          location: 'run.py:36 in load_games',
        },
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
      }],
    },
  })

  render(<CalculateValues />)

  await user.click(await screen.findByRole('button', {
    name: 'Show failure details for College Womens Basketball',
  }))

  expect(screen.getByRole('img', { name: 'Failed' }).closest('.text-danger')).toBeInTheDocument()
  expect(await screen.findByText('Failure details')).toBeInTheDocument()
  expect(screen.getByText(/No games were found for the selected dataset/)).toBeInTheDocument()
  expect(screen.getByText(/run\.py:36 in load_games/)).toBeInTheDocument()

  await user.click(screen.getByText('Last 5 Execution History'))

  await waitFor(() => {
    expect(screen.queryByText('Failure details')).not.toBeInTheDocument()
  })
})

test('refreshes start time, finish time, and latest status for an execution', async () => {
  const queuedRecord = {
    task_id: 'changing-run',
    queued_at: '2026-10-01T12:00:00Z',
    started_at: null,
    finished_at: null,
    sport_type: 'basketball',
    gender: 'womens',
    level: 'college',
    iterations: 2,
    status: 'queued',
  }
  api.get
    .mockResolvedValueOnce({ data: { algorithm: [queuedRecord] } })
    .mockResolvedValueOnce({
      data: {
        algorithm: [{
          ...queuedRecord,
          started_at: '2026-10-01T12:00:01Z',
          finished_at: '2026-10-01T12:00:12Z',
          status: 'complete',
        }],
      },
    })
  api.post.mockResolvedValue({ data: { task_id: 'new-run' } })

  render(<CalculateValues />)

  expect(await screen.findByText('Queued')).toBeInTheDocument()
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 3100))
  })

  const row = screen.getByRole('row', { name: /College Womens Basketball/ })
  const cells = within(row).getAllByRole('cell')
  expect(cells[3]).not.toHaveTextContent('N/A')
  expect(cells[4]).not.toHaveTextContent('N/A')
  expect(cells[5]).toHaveTextContent('0H 0M 11S')
  expect(cells[6]).toHaveTextContent('Complete')
  expect(screen.getByText('Last 5 Execution History')).toBeInTheDocument()
})

test('starts an algorithm run for the selected dataset', async () => {
  api.get.mockResolvedValue({ data: { algorithm: [] } })
  api.post.mockResolvedValue({ data: { task_id: 'new-run' } })

  render(<CalculateValues />)
  fireEvent.click(screen.getByRole('button', { name: 'Run Algorithm' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/run_algorithm/1/?sport_type=basketball&gender=womens&level=college',
    {},
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  ))
})

test('loads z-score history and starts it from its separate view', async () => {
  api.get.mockResolvedValue({
    data: {
      algorithm: [],
      z_scores: [{
        task_id: 'z-score-history',
        queued_at: '2026-10-01T12:00:00Z',
        started_at: null,
        finished_at: null,
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
        status: 'queued',
      }],
    },
  })
  api.post.mockResolvedValue({ data: { task_id: 'new-z-score-run' } })

  render(<CalculateValues view="z-score" />)

  expect(screen.getByRole('heading', { name: 'Z-Score' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Run Algorithm' })).not.toBeInTheDocument()
  expect(screen.queryByText('Last 5 Execution History')).not.toBeInTheDocument()
  expect(await screen.findByText('Last 5 z-Score Execution History')).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Job' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Elapsed Time' })).toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Process' })).not.toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'College Womens Basketball' })).toBeInTheDocument()
  const queuedRow = screen.getByRole('row', { name: /College Womens Basketball/ })
  expect(within(queuedRow).getAllByRole('cell')[4]).toHaveTextContent('N/A')
  expect(screen.getByRole('cell', { name: 'Queued' })).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Calculate z Scores' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/calc_z_scores/?sport_type=basketball&gender=womens&level=college',
    {},
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  ))
})
