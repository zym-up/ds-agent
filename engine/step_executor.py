"""分析步骤调度器 — Streamlit 和 FastAPI 共用入口

支持两种调用模式：
1. method 模式：params.method 指定原子操作 → 只执行该操作
2. 默认模式：无 method → 执行全量流水线（向后兼容）
"""
import json
import pandas as pd
from engine.data_cleaner import clean_pipeline, remove_duplicates, fill_missing, detect_outliers
from engine.eda import eda_pipeline, scatter_plot, line_plot, correlation_matrix, \
    distribution_plot, pair_plot, describe
from engine.modeler import train_regression, evaluate_regression, split_data, feature_importance, residual_plot

_MODEL_ALIASES = {
    "random_forest_regressor": "random_forest", "randomforest": "random_forest",
    "random_forest": "random_forest",
    "xgboost_regressor": "xgboost", "xgb": "xgboost", "xgboost": "xgboost",
    "linear_regression": "linear", "linear": "linear",
    "ridge_regression": "ridge", "ridge": "ridge",
    "lasso_regression": "lasso", "lasso": "lasso",
}


def _resolve_xy(params: dict, numeric_cols: list) -> tuple:
    """从 params 中解析 x/y 列：优先用 x/y 参数，缺一个时从 columns 补全，都没有则从 columns 取前两列"""
    x = params.get("x")
    y = params.get("y")
    if x and y:
        return x, y
    cols = params.get("columns")
    if isinstance(cols, list) and len(cols) >= 2:
        if x and not y:
            # 有 x 缺 y：从 columns 中找第一个不为 x 的列作为 y
            for c in cols:
                if c != x:
                    return x, c
        elif y and not x:
            # 有 y 缺 x：从 columns 中找第一个不为 y 的列作为 x
            for c in cols:
                if c != y:
                    return c, y
        else:
            # 都没有：取 columns 前两列
            return cols[0], cols[1]
    return None, None


def execute_step(step_type: str, params: dict, df: pd.DataFrame) -> dict:
    """执行单个分析步骤，返回 {charts, text, metrics, result_df}

    params 中可指定 method 来选择原子操作；
    不指定 method 时走默认全量流水线（向后兼容）。
    """
    method = params.get("method")
    charts = []
    text = ""
    metrics = {}
    result_df = df

    if step_type == "clean":
        result = _clean(method, params, df)
        charts, text, metrics, result_df = result["charts"], result["text"], result["metrics"], result["result_df"]

    elif step_type == "eda":
        result = _eda(method, params, df)
        charts, text, metrics = result["charts"], result["text"], result["metrics"]

    elif step_type == "feature":
        result = _feature(method, params, df)
        charts, text, metrics, result_df = result["charts"], result["text"], result["metrics"], result["result_df"]

    elif step_type == "model":
        result = _model(method, params, df)
        charts, text, metrics = result["charts"], result["text"], result["metrics"]

    elif step_type == "report":
        text = "报告生成请使用「📋 导出报告」功能。"

    return {"charts": charts, "text": text, "metrics": metrics, "result_df": result_df}


# ──────────────────────────────────────────────
# clean — 数据清洗
# ──────────────────────────────────────────────

def _clean(method, params, df):
    if method == "dedup":
        subset = params.get("subset")
        result_df, info = remove_duplicates(df, subset=subset)
        before = info.get("去重前", list(info.values())[0] if info else "?")
        after = info.get("去重后", list(info.values())[1] if len(info) > 1 else "?")
        removed = info.get("删除重复行数", list(info.values())[2] if len(info) > 2 else "?")
        text = f"### 去重完成\n- 去重前: {before}\n- 去重后: {after}\n- 删除: {removed} 行"
        metrics = info
        return {"charts": [], "text": text, "metrics": metrics, "result_df": result_df}

    elif method == "fill_missing":
        columns = params.get("columns")
        strategy = params.get("strategy", "mean")
        fill_value = params.get("fill_value")
        result_df, info = fill_missing(df, strategy=strategy, columns=columns, fill_value=fill_value)
        text = f"### 缺失值填充\n- 策略: {info['策略']}\n- 填充列: {json.dumps(info['填充列'], ensure_ascii=False)}"
        metrics = info
        return {"charts": [], "text": text, "metrics": metrics, "result_df": result_df}

    elif method == "detect_outliers":
        columns = params.get("columns")
        outlier_method = params.get("outlier_method", "iqr")
        threshold = params.get("threshold", 1.5)
        info = detect_outliers(df, method=outlier_method, columns=columns, threshold=threshold)
        total = sum(v["count"] for v in info.values())
        text = f"### 异常值检测\n- 方法: {outlier_method}\n- 总异常值数: {total}\n```json\n{json.dumps(info, ensure_ascii=False, indent=2)}\n```"
        metrics = info
        return {"charts": [], "text": text, "metrics": metrics, "result_df": df}

    elif method == "drop_columns":
        drop_cols = params.get("columns", [])
        existing = [c for c in drop_cols if c in df.columns]
        result_df = df.drop(columns=existing)
        text = f"### 删除列\n- 已删除: {', '.join(existing)}"
        metrics = {"删除列": existing}
        return {"charts": [], "text": text, "metrics": metrics, "result_df": result_df}

    else:
        # 默认：全量清洗流水线
        clean_params = {}
        if "columns" in params:
            clean_params["fill_columns"] = params["columns"]
            clean_params["outlier_columns"] = params["columns"]
        if "handle_outliers" in params:
            clean_params["outlier_method"] = params["handle_outliers"].lower()
        if "handle_missing" in params:
            if params["handle_missing"] == "drop":
                df = df.dropna(subset=params.get("columns"))
            else:
                clean_params["fill_strategy"] = params["handle_missing"]
        result_df, summary = clean_pipeline(df, **clean_params)
        text = f"### 数据清洗完成\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"
        return {"charts": [], "text": text, "metrics": summary, "result_df": result_df}


# ──────────────────────────────────────────────
# eda — 探索性分析
# ──────────────────────────────────────────────

def _eda(method, params, df):
    numeric_cols = params.get("columns") or df.select_dtypes(include=["number"]).columns.tolist()

    if method == "correlation":
        corr_method = params.get("corr_method", "pearson")
        _, fig = correlation_matrix(df, method=corr_method, columns=numeric_cols)
        text = f"### 相关性矩阵 ({corr_method})\n- 分析列数: {len(numeric_cols)}"
        return {"charts": [fig], "text": text, "metrics": {"列数": len(numeric_cols)}}

    elif method == "distribution":
        cols = numeric_cols[:6]
        figs = [distribution_plot(df, col) for col in cols]
        text = f"### 分布分析\n- 分析列: {', '.join(cols)}"
        return {"charts": figs, "text": text, "metrics": {"列数": len(cols)}}

    elif method == "scatter":
        x_col, y_col = _resolve_xy(params, numeric_cols)
        if not x_col or not y_col:
            return {"charts": [], "text": "### 散点图\n- 错误: 未指定 x 或 y 轴列，请在 params 中传入 x 和 y（或在 columns 中至少放两列）", "metrics": {}}
        if x_col not in df.columns or y_col not in df.columns:
            return {"charts": [], "text": f"### 散点图\n- 错误: 列 '{x_col}' 或 '{y_col}' 不存在", "metrics": {}}
        fig = scatter_plot(df, x=x_col, y=y_col,
                           color=params.get("color"), trendline=params.get("trendline", True))
        text = f"### 散点图: {x_col} vs {y_col}"
        return {"charts": [fig], "text": text, "metrics": {"x": x_col, "y": y_col}}

    elif method == "line":
        x_col, y_col = _resolve_xy(params, numeric_cols)
        if not x_col or not y_col:
            return {"charts": [], "text": "### 折线图\n- 错误: 未指定 x 或 y 轴列，请在 params 中传入 x 和 y（或在 columns 中至少放两列）", "metrics": {}}
        if x_col not in df.columns or y_col not in df.columns:
            return {"charts": [], "text": f"### 折线图\n- 错误: 列 '{x_col}' 或 '{y_col}' 不存在", "metrics": {}}
        fig = line_plot(df, x=x_col, y=y_col, group_by=params.get("group_by"))
        text = f"### 折线图: {y_col} vs {x_col}"
        if params.get("group_by"):
            text += f" (按 {params['group_by']} 分组)"
        return {"charts": [fig], "text": text, "metrics": {"x": x_col, "y": y_col}}

    elif method == "multi_line":
        # 支持两种模式：
        # 1. pairs 模式：[[x1,y1], [x2,y2], ...] — 指定任意列对
        # 2. x + columns 模式：公共 x 轴，对每个 y 列生成一张折线图
        pairs = params.get("pairs")
        if pairs and isinstance(pairs, list) and all(isinstance(p, list) and len(p) >= 2 for p in pairs):
            figs = []
            labels = []
            for p in pairs:
                xc, yc = p[0], p[1]
                if xc in df.columns and yc in df.columns:
                    figs.append(line_plot(df, x=xc, y=yc, group_by=params.get("group_by")))
                    labels.append(f"{yc} vs {xc}")
            if not figs:
                return {"charts": [], "text": "### 多列折线图\n- 错误: 指定的列对均无效", "metrics": {}}
            text = f"### 多列折线图\n- {', '.join(labels)}"
            return {"charts": figs, "text": text, "metrics": {"列对数": len(figs)}}

        x_col, first_y = _resolve_xy(params, numeric_cols)
        y_cols = params.get("columns") or ([first_y] if first_y else [])
        if not x_col or not y_cols:
            return {"charts": [], "text": "### 多列折线图\n- 错误: 请指定 pairs（列对列表）或 x+columns（公共横轴+纵轴列表）", "metrics": {}}
        figs = []
        for yc in y_cols:
            if yc in df.columns and yc != x_col:
                figs.append(line_plot(df, x=x_col, y=yc, group_by=params.get("group_by")))
        if not figs:
            return {"charts": [], "text": "### 多列折线图\n- 错误: 没有有效的纵轴列", "metrics": {}}
        text = f"### 多列折线图\n- 横轴: {x_col}\n- 纵轴: {', '.join(y_cols[:10])}"
        return {"charts": figs, "text": text, "metrics": {"横轴": x_col, "纵轴列数": len(y_cols)}}

    elif method == "pairplot":
        cols = numeric_cols[:6] if len(numeric_cols) > 6 else numeric_cols
        fig = pair_plot(df, cols)
        text = f"### 配对散点矩阵\n- 分析列: {', '.join(cols)}"
        return {"charts": [fig], "text": text, "metrics": {"列数": len(cols)}}

    elif method == "describe":
        text = describe(df, numeric_cols)
        return {"charts": [], "text": text, "metrics": {"列数": len(numeric_cols)}}

    else:
        # 默认：检查是否隐含散点图/折线图参数
        chart_type = params.get("chart_type", "full")
        has_xy = params.get("x") and params.get("y")

        if chart_type == "line" and has_xy:
            fig = line_plot(df, x=params["x"], y=params["y"], group_by=params.get("group_by"))
            text = f"### 折线图: {params['y']} vs {params['x']}"
            return {"charts": [fig], "text": text, "metrics": {"x": params["x"], "y": params["y"]}}

        elif chart_type == "scatter" or has_xy:
            fig = scatter_plot(df, x=params["x"], y=params["y"],
                               color=params.get("color"), trendline=params.get("trendline", True))
            text = f"### 散点图: {params['x']} vs {params['y']}"
            return {"charts": [fig], "text": text, "metrics": {"x": params["x"], "y": params["y"]}}

        # 全量 EDA 流水线
        result = eda_pipeline(df, numeric_columns=numeric_cols)
        text = f"### 探索性分析\n- 行数: {result['row_count']}\n- 列数: {result['column_count']}"
        numeric_col_count = len(result.get("numeric_stats", {}))
        cat_col_count = len(result.get("categorical_stats", {}))
        return {"charts": result["charts"], "text": text,
                "metrics": {"行数": result["row_count"], "列数": result["column_count"],
                            "数值列数": numeric_col_count, "分类列数": cat_col_count}}


# ──────────────────────────────────────────────
# feature — 特征工程
# ──────────────────────────────────────────────

def _feature(method, params, df):
    from engine.feature_engineer import scale_features, encode_categorical, select_by_variance, select_by_correlation

    if method == "scale":
        cols = params.get("columns", [])
        scale_method = params.get("scale_method", "standard")
        if not cols:
            return {"charts": [], "text": "### 标准化\n- 错误: 未指定 columns", "metrics": {}, "result_df": df}
        result_df, summary = scale_features(df, cols, scale_method)
        text = f"### 标准化 ({summary['方法']})\n- 处理列: {', '.join(summary['处理列'])}"
        return {"charts": [], "text": text, "metrics": {"标准化": summary}, "result_df": result_df}

    elif method == "encode":
        cols = params.get("columns", [])
        encode_method = params.get("encode_method", "onehot")
        if not cols:
            return {"charts": [], "text": "### 编码\n- 错误: 未指定 columns", "metrics": {}, "result_df": df}
        result_df, summary = encode_categorical(df, cols, encode_method)
        text = f"### 编码 ({summary['方法']})\n- 处理列: {', '.join(summary['处理列'])}"
        return {"charts": [], "text": text, "metrics": {"编码": summary}, "result_df": result_df}

    elif method == "variance_filter":
        threshold = params.get("threshold", 0.01)
        result_df, summary = select_by_variance(df, threshold)
        text = f"### 方差过滤 (阈值={summary['阈值']})\n- 保留 {len(summary['保留特征'])} 个\n- 移除: {', '.join(summary['移除特征'][:20])}"
        return {"charts": [], "text": text, "metrics": {"方差过滤": summary}, "result_df": result_df}

    elif method == "correlation_select":
        target = params.get("target", "")
        k = params.get("k", 10)
        sel_method = params.get("sel_method", "f_regression")
        if not target or target not in df.columns:
            return {"charts": [], "text": f"### 相关性选择\n- 错误: 目标列 '{target}' 不存在", "metrics": {}, "result_df": df}
        selected, summary = select_by_correlation(df, target, k, sel_method)
        text = f"### 相关性选择 (目标={target})\n- TOP {len(selected)} 特征: {', '.join(selected[:10])}"
        return {"charts": [], "text": text, "metrics": {"相关性选择": summary}, "result_df": df}

    else:
        # 默认：特征工程全流程
        text_parts = ["### 特征工程结果"]
        result_df = df.copy()

        scale_params = params.get("scale")
        if scale_params:
            cols = scale_params.get("columns", [])
            sm = scale_params.get("method", "standard")
            if cols:
                result_df, summary = scale_features(result_df, cols, sm)
                text_parts.append(f"- 标准化 ({summary['方法']}): {', '.join(summary['处理列'])}")
                metrics["标准化"] = summary

        encode_params = params.get("encode")
        if encode_params:
            cols = encode_params.get("columns", [])
            em = encode_params.get("method", "onehot")
            if cols:
                result_df, summary = encode_categorical(result_df, cols, em)
                text_parts.append(f"- 编码 ({summary['方法']}): {', '.join(summary['处理列'])}")
                metrics["编码"] = summary

        variance_threshold = params.get("variance_threshold")
        if variance_threshold:
            result_df, summary = select_by_variance(result_df, variance_threshold)
            text_parts.append(f"- 方差过滤 (阈值={summary['阈值']}): 保留 {len(summary['保留特征'])} 个, 移除 {len(summary['移除特征'])} 个")
            metrics["方差过滤"] = summary

        corr_params = params.get("correlation")
        if corr_params:
            target = corr_params.get("target", "")
            k = corr_params.get("k", 10)
            cm = corr_params.get("method", "f_regression")
            if target and target in result_df.columns:
                selected, summary = select_by_correlation(result_df, target, k, cm)
                text_parts.append(f"- 相关性选择 (目标={target}): TOP {len(selected)} 特征")
                text_parts.append(f"  选中特征: {', '.join(selected[:10])}")
                metrics["相关性选择"] = summary

        text = "\n".join(text_parts)
        return {"charts": [], "text": text, "metrics": metrics, "result_df": result_df}


# ──────────────────────────────────────────────
# model — 建模
# ──────────────────────────────────────────────

def _model(method, params, df):
    target = params.get("target", "")
    raw_type = params.get("model_type", "linear")
    model_type = _MODEL_ALIASES.get(raw_type, raw_type)
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target]

    if not target:
        return {"charts": [], "text": "### 建模\n- 错误: 未指定 target", "metrics": {}}

    model_df = df[numeric_cols + [target]].dropna()
    X_train, X_test, y_train, y_test = split_data(model_df, target)
    model, _ = train_regression(X_train, y_train, model_type)

    if method == "train":
        eval_metrics = evaluate_regression(model, X_test, y_test)
        text = f"### 建模结果 ({model_type})\n"
        for k, v in eval_metrics.items():
            text += f"- {k}: {v}\n"
        return {"charts": [], "text": text, "metrics": eval_metrics}

    elif method == "importance":
        _, imp_fig = feature_importance(model, numeric_cols)
        text = f"### 特征重要性 ({model_type})\n- 目标: {target}\n- 特征数: {len(numeric_cols)}"
        return {"charts": [imp_fig], "text": text, "metrics": {"特征数": len(numeric_cols)}}

    elif method == "residual":
        y_pred = model.predict(X_test)
        res_fig = residual_plot(y_test, y_pred)
        text = f"### 残差诊断 ({model_type})\n- 目标: {target}"
        return {"charts": [res_fig], "text": text, "metrics": {}}

    else:
        # 默认：全量建模流水线
        eval_metrics = evaluate_regression(model, X_test, y_test)
        _, imp_fig = feature_importance(model, numeric_cols)
        y_pred = model.predict(X_test)
        res_fig = residual_plot(y_test, y_pred)

        text = f"### 建模结果 ({model_type})\n"
        for k, v in eval_metrics.items():
            text += f"- {k}: {v}\n"
        return {"charts": [imp_fig, res_fig], "text": text, "metrics": eval_metrics}
