import { legacy_createStore as createStore } from 'redux'
import { persistStore, persistReducer } from 'redux-persist'
import storage from 'redux-persist/lib/storage'

const initialState = {
  sidebarShow: true,
  theme: 'light',
  isAdmin: false,
  authReady: false,
  sport: "football",
  gender: "mens",
  level: "high_school",
}

const changeState = (state = initialState, { type, payload }) => {
  switch (type) {
    case 'set':
      return { ...state, ...payload }
    case 'login':
      return { ...state, isAdmin: true, authReady: true }
    case 'logout':
      return { ...state, isAdmin: false, authReady: true }
    case 'updateAdminState':
      return { ...state, ...payload }
    default:
      return state
  }
}

const persistConfig = {
  key: 'root',
  storage,
  blacklist: ['isAdmin', 'authReady'],
}

const persistedReducer = persistReducer(persistConfig, changeState)

export const store = createStore(persistedReducer);
export const persistor = persistStore(store);
