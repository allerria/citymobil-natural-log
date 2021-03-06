import joblib
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from loguru import logger
from sklearn.pipeline import Pipeline
from vecstack import StackingTransformer
from xgboost import XGBRegressor

from utils import xgb_params, lgb_params, cat_params, WeightedRegressor, mean_absolute_percentage_error, \
    PROCESSED_DATA

X_train, y_train, X_val, y_val, X_test, Test_ID = joblib.load(PROCESSED_DATA)

estimators = [
    ('xgb', XGBRegressor(**xgb_params)),
    ('lgb', LGBMRegressor(**lgb_params)),
    ('cat', CatBoostRegressor(**cat_params))
]

final_estimator = WeightedRegressor()

stack = StackingTransformer(estimators=estimators, variant='A', regression=True, n_folds=5, shuffle=False,
                            random_state=None)
steps = [('stack', stack),
         ('final_estimator', final_estimator)]
pipe = Pipeline(steps)

logger.info('start training...')

pipe.fit(X_train, y_train)

logger.info('end training.')

y_pred = pipe.predict(X_val)
logger.info(f'MAPE on valid: {mean_absolute_percentage_error(y_val, y_pred)}')

y_test = pipe.predict(X_test)

df = pd.DataFrame([])
df['Prediction'] = y_test
df['Id'] = Test_ID
df_test = df[['Id', 'Prediction']]
df_test.to_csv('data/submission_new.csv', index=None)

logger.info('the end!')
