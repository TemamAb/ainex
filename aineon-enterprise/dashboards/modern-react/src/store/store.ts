import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import systemReducer from './slices/systemSlice'
import profitReducer from './slices/profitSlice'
import analyticsReducer from './slices/analyticsSlice'
import operationsReducer from './slices/operationsSlice'
import riskReducer from './slices/riskSlice'
import tradingReducer from './slices/tradingSlice'
import complianceReducer from './slices/complianceSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    system: systemReducer,
    profit: profitReducer,
    analytics: analyticsReducer,
    operations: operationsReducer,
    risk: riskReducer,
    trading: tradingReducer,
    compliance: complianceReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
