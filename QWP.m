clear; clc; close all;

%% 步驟 1: 讀取 Excel 數據
filename = 'polar_data.xlsx';
sheetName = 'QWP';   % 如果工作表名稱不同，請修改這裡

% A欄: PL2角度
% B欄: QWP = 30 degree
% C欄: QWP = 45 degree
% D欄: QWP = 60 degree
data = readmatrix(filename, 'Sheet', sheetName, 'Range', 'A1:D36');

theta_PL2 = data(:, 1);      % 偏振片 PL2 角度
I_data    = data(:, 2:4);    % 三組強度數據

QWP_angles = [30, 45, 60];   % 三組 QWP 標稱角度
numGroups = length(QWP_angles);

disp('數據讀取完成！共 36 筆角度，3 組 QWP 數據。');

%% 步驟 2: 建立全域擬合資料

theta_all = [];
I_all = [];
group_all = [];

for i = 1:numGroups

    I_raw = I_data(:, i);

    valid_idx = ~isnan(theta_PL2) & ~isnan(I_raw);

    theta_all = [theta_all; theta_PL2(valid_idx)];
    I_all     = [I_all; I_raw(valid_idx)];
    group_all = [group_all; i * ones(sum(valid_idx), 1)];

end

% xdata 第一欄：PL2 角度
% xdata 第二欄：組別 1, 2, 3
xdata = [theta_all, group_all];

%% 步驟 3: 定義 QWP 擬合模型
%
% 全域參數：
% p(1) = I_bg，全域共用
% p(2) = I0，全域共用
%
% 各組角度修正：
% QWP = 30°:
% p(3) = delta_QWP,30
% p(4) = delta_PL2,30
%
% QWP = 45°:
% p(5) = delta_QWP,45
% p(6) = delta_PL2,45
%
% QWP = 60°:
% p(7) = delta_QWP,60
% p(8) = delta_PL2,60

modelFun = @(p, x) qwpModelGlobalIntensity(p, x, QWP_angles);

%% 步驟 4: 初始猜測值

I_min_all = min(I_all);
I_max_all = max(I_all);
I_mean_all = mean(I_all);

I0_guess = 2 * (I_max_all - I_min_all);
I_bg_guess = I_mean_all - I0_guess / 2;

p0 = [
    I_bg_guess, ...   % I_bg，全域
    I0_guess, ...     % I0，全域
    0, 0, ...         % delta_QWP,30, delta_PL2,30
    0, 0, ...         % delta_QWP,45, delta_PL2,45
    0, 0              % delta_QWP,60, delta_PL2,60
];

%% 步驟 5: 設定上下界並執行擬合

% I0 >= 0
% delta_QWP 限制在 -45° 到 45°
% delta_PL2 限制在 -90° 到 90°

lb = [-Inf, 0, ...
      -45, -90, ...
      -45, -90, ...
      -45, -90];

ub = [ Inf, Inf, ...
       45, 90, ...
       45, 90, ...
       45, 90];

options = optimoptions('lsqcurvefit', ...
    'Display', 'iter', ...
    'MaxIterations', 1000);

[p_fit, resnorm] = lsqcurvefit(modelFun, p0, xdata, I_all, lb, ub, options);

I_bg_global = p_fit(1);
I0_global   = p_fit(2);

fprintf('\n=== QWP 擬合結果：I_bg 與 I0 為全域參數 ===\n');
fprintf('全域背景光 I_bg = %.6f mW\n', I_bg_global);
fprintf('全域強度 I0     = %.6f mW\n', I0_global);
fprintf('總殘差平方和    = %.6f\n', resnorm);

%% 步驟 6: 分別計算三組擬合曲線與 R^2

theta_fine = 0:0.1:360;
I_fitted_all = zeros(numGroups, length(theta_fine));
R_squared_all = zeros(numGroups, 1);

fprintf('\n=== 各組角度修正結果 ===\n');

for i = 1:numGroups

    theta_QWP_nominal = QWP_angles(i);

    idx_delta = 2*i + 1;

    delta_QWP = p_fit(idx_delta);
    delta_PL2 = p_fit(idx_delta + 1);

    I_raw = I_data(:, i);
    valid_idx = ~isnan(theta_PL2) & ~isnan(I_raw);

    theta_use = theta_PL2(valid_idx);
    I_use     = I_raw(valid_idx);

    % 擬合曲線
    xfine_i = [theta_fine(:), i * ones(length(theta_fine), 1)];
    I_fitted_all(i, :) = modelFun(p_fit, xfine_i);

    % 預測原始點
    xuse_i = [theta_use, i * ones(length(theta_use), 1)];
    I_pred = modelFun(p_fit, xuse_i);

    SS_tot = sum((I_use - mean(I_use)).^2);
    SS_res = sum((I_use - I_pred).^2);

    if SS_tot > 0
        R_squared = 1 - SS_res / SS_tot;
    else
        R_squared = NaN;
    end

    R_squared_all(i) = R_squared;

    fprintf('\nQWP = %d°\n', theta_QWP_nominal);
    fprintf('QWP 零點誤差 delta_QWP = %.3f °\n', delta_QWP);
    fprintf('PL2 零點誤差 delta_PL2 = %.3f °\n', delta_PL2);
    fprintf('QWP 實際角度          = %.3f °\n', theta_QWP_nominal + delta_QWP);
    fprintf('R^2                  = %.4f\n', R_squared);

end

%% 步驟 7: XY 關係圖

fig1 = figure('Name', 'QWP - Global Ibg I0 Fit - XY Plot', ...
              'Position', [100 100 1150 750]);

hold on;

colors = [
    0.0000 0.4470 0.7410;
    0.8500 0.3250 0.0980;
    0.4660 0.6740 0.1880
];

markerTypes = {'o', 's', '^'};

for i = 1:numGroups

    theta_QWP_nominal = QWP_angles(i);
    I_raw = I_data(:, i);

    valid_idx = ~isnan(theta_PL2) & ~isnan(I_raw);

    theta_use = theta_PL2(valid_idx);
    I_use     = I_raw(valid_idx);

    % 原始散佈點
    scatter(theta_use, I_use, 45, colors(i, :), markerTypes{i}, ...
        'filled', ...
        'MarkerFaceAlpha', 0.75, ...
        'MarkerEdgeColor', 'k', ...
        'DisplayName', sprintf('QWP = %d° 原始數據', theta_QWP_nominal));

    % 擬合曲線
    plot(theta_fine, I_fitted_all(i, :), '-', ...
        'Color', colors(i, :), ...
        'LineWidth', 2.5, ...
        'DisplayName', sprintf('QWP = %d° 擬合曲線', theta_QWP_nominal));

end

grid on;

xlabel('偏振片角度 \theta_{PL2} (degree)');
ylabel('強度 I (mW)');
title('不同 QWP 角度下的擬合結果：I_{bg} 與 I_0 為全域參數');

legend('Location', 'bestoutside');

xlim([0 360]);
ylim([0 max(I_data(:), [], 'omitnan') * 1.15]);

%% 步驟 8: 加上文字框

text_str = cell(numGroups + 2, 1);

text_str{1} = ['$I=I_{bg}+\frac{I_0}{2}[1+\cos(2(\theta_{QWP}+\delta_{QWP}))' ...
               '\cos(2(\theta_{PL2}+\delta_{PL2})-2(\theta_{QWP}+\delta_{QWP}))]$'];

text_str{2} = sprintf('$I_{bg}=%.4g$ mW, $I_0=%.4g$ mW', ...
                      I_bg_global*1000, I0_global*1000);

for i = 1:numGroups

    theta_QWP_nominal = QWP_angles(i);

    idx_delta = 2*i + 1;

    delta_QWP = p_fit(idx_delta);
    delta_PL2 = p_fit(idx_delta + 1);
    R2        = R_squared_all(i);

    text_str{i+2} = sprintf( ...
        'QWP $=%d^\\circ$: $\\delta_Q=%.2f^\\circ$, $\\delta_P=%.2f^\\circ$, $R^2=%.4f$', ...
        theta_QWP_nominal, delta_QWP, delta_PL2, R2);

end

annotation('textbox', ...
    'Position', [0.07 0.68 0.52 0.21], ...
    'String', text_str, ...
    'Interpreter', 'latex', ...
    'FontSize', 10.2, ...
    'FontWeight', 'bold', ...
    'BackgroundColor', [1 1 1 0.9], ...
    'EdgeColor', [0.4 0.4 0.4], ...
    'LineWidth', 1, ...
    'HorizontalAlignment', 'left', ...
    'VerticalAlignment', 'top');

%% 步驟 9: 極化圖 Polar Plot

fig2 = figure('Name', 'QWP - Global Ibg I0 Fit - Polar Plot', ...
              'Position', [950 100 850 850]);

polaraxes;
hold on;

for i = 1:numGroups

    theta_QWP_nominal = QWP_angles(i);
    I_raw = I_data(:, i);

    valid_idx = ~isnan(theta_PL2) & ~isnan(I_raw);

    theta_use = theta_PL2(valid_idx);
    I_use     = I_raw(valid_idx);

    % 擬合曲線
    polarplot(deg2rad(theta_fine), I_fitted_all(i, :), '-', ...
        'Color', colors(i, :), ...
        'LineWidth', 2.5, ...
        'DisplayName', sprintf('QWP = %d° 擬合曲線', theta_QWP_nominal));

    % 原始數據點
    polarscatter(deg2rad(theta_use), I_use, 45, colors(i, :), ...
        markerTypes{i}, ...
        'filled', ...
        'MarkerEdgeColor', 'k', ...
        'DisplayName', sprintf('QWP = %d° 原始數據', theta_QWP_nominal));

end

title('不同 QWP 角度下的極化圖');

legend('Location', 'bestoutside');

thetaticks(0:30:360);

%% 步驟 10: 自動儲存兩張圖

figure(fig1);
exportgraphics(fig1, 'QWP_XY_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

figure(fig2);
exportgraphics(fig2, 'QWP_Polar_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

disp('兩張圖已儲存到目前工作目錄：');
disp('  1. QWP_XY_Plot.png');
disp('  2. QWP_Polar_Plot.png');

%% ===== Local function：I_bg 與 I0 全域共用的 QWP 模型 =====

function I = qwpModelGlobalIntensity(p, x, QWP_angles)

    theta_PL2 = x(:, 1);
    group_idx = x(:, 2);

    I = zeros(size(theta_PL2));

    I_bg_global = p(1);
    I0_global   = p(2);

    for k = 1:length(QWP_angles)

        idx_group = group_idx == k;

        idx_delta = 2*k + 1;

        delta_QWP = p(idx_delta);
        delta_PL2 = p(idx_delta + 1);

        theta_QWP_nominal = QWP_angles(k);

        theta_QWP_true = theta_QWP_nominal + delta_QWP;
        theta_PL2_true = theta_PL2(idx_group) + delta_PL2;

        I(idx_group) = I_bg_global + (I0_global/2) .* ...
            (1 + cosd(2*theta_QWP_true) .* ...
            cosd(2*theta_PL2_true - 2*theta_QWP_true));

    end

end