clear; clc; close all;

%% 步驟 1: 讀取 Excel 數據

filename = 'polar_data.xlsx';
sheetName = 'Sheet1';

% U欄: theta
% V欄: I
data = readmatrix(filename, 'Sheet', sheetName, 'Range', 'U6:V41');

theta_deg = data(:, 1);      % 角度 θ (degree)
I_raw     = data(:, 2);      % 單組強度量測

%% 忽略 theta = 210, 220，以及空白 / NaN 資料

valid_idx = ~isnan(theta_deg) & ~isnan(I_raw) & ...
            theta_deg ~= 210 & theta_deg ~= 220;

theta_deg = theta_deg(valid_idx);
I_raw     = I_raw(valid_idx);

fprintf('數據讀取完成！有效數據共 %d 筆。\n', length(theta_deg));
disp('已忽略 theta = 210°、220° 以及空白資料。');

%% 步驟 2: 定義擬合模型
% I(theta) = I_bg + I0 cos^2(2theta - theta0)

modelFun = @(p, th) p(1) + p(2) .* (cosd(2.*th - p(3))).^2;

% 初始猜測值
% theta0 約等於 2 * 最大強度位置
[~, max_idx] = max(I_raw);
theta_max_guess = theta_deg(max_idx);

p0 = [
    min(I_raw), ...
    max(I_raw) - min(I_raw), ...
    2 * theta_max_guess
];

%% 步驟 3: 非線性擬合

options = optimoptions('lsqcurvefit', ...
    'Display', 'iter', ...
    'MaxIterations', 500);

% 限制 I0 >= 0，避免擬合出負振幅造成相位判讀混亂
lb = [-Inf, 0, -Inf];
ub = [ Inf, Inf, Inf];

[p_fit, resnorm] = lsqcurvefit(modelFun, p0, theta_deg, I_raw, lb, ub, options);

I_bg   = p_fit(1);
I0_fit = p_fit(2);
theta0 = p_fit(3);

fprintf('\n=== 擬合結果 ===\n');
fprintf('背景光 I_bg     = %.6f mW\n', I_bg);
fprintf('振幅 I0_fit     = %.6f mW\n', I0_fit);
fprintf('相位 theta0     = %.3f °\n', theta0);
fprintf('殘差平方和      = %.6f\n', resnorm);

%% 步驟 4: 生成擬合曲線

theta_fine = 0:0.1:360;

I_fitted = modelFun(p_fit, theta_fine);

%% 步驟 5: 計算 R²

I_pred = modelFun(p_fit, theta_deg);

SS_tot = sum((I_raw - mean(I_raw)).^2);
SS_res = sum((I_raw - I_pred).^2);

R_squared = 1 - SS_res / SS_tot;

fprintf('R^2             = %.4f\n', R_squared);

%% 步驟 6: XY 關係圖

fig1 = figure('Name', 'Malus''s Law - XY Plot', ...
              'Position', [100 100 1000 700]);

scatter(theta_deg, I_raw, 45, 'b', 'filled', ...
        'MarkerFaceAlpha', 0.75, ...
        'MarkerEdgeColor', 'k', ...
        'DisplayName', '原始量測數據');

hold on;

plot(theta_fine, I_fitted, 'r-', 'LineWidth', 2.5, ...
     'DisplayName', '擬合曲線 I_{bg} + I_0 cos^2(2\theta - \theta_0)');

grid on;

xlabel('角度 \theta (degree)');
ylabel('強度 I (mW)');
title('Malus''s Law 曲線擬合結果');

legend('Location', 'northwest');

xlim([0 360]);
ylim([0 max(I_raw) * 1.15]);

%% 加上擬合公式與 R² 文字框

eq_str = sprintf('$I = %.4f + %.4f\\cos^{2}(2\\theta - %.3f^{\\circ}) mW$', ...
                 I_bg*1000, I0_fit*1000, theta0);

r2_str = sprintf('$R^{2} = %.4f$', R_squared);

text_str = {eq_str; r2_str};

annotation('textbox', ...
    'Position', [0.52 0.82 0.42 0.08], ...
    'String', text_str, ...
    'Interpreter', 'latex', ...
    'FontSize', 12, ...
    'FontWeight', 'bold', ...
    'BackgroundColor', [1 1 1 0.9], ...
    'EdgeColor', [0.4 0.4 0.4], ...
    'LineWidth', 1, ...
    'HorizontalAlignment', 'left', ...
    'VerticalAlignment', 'top');

%% 步驟 7: 極化圖 Polar Plot

fig2 = figure('Name', 'Malus''s Law - Polar Plot', ...
              'Position', [950 100 800 800]);

polaraxes;

polarplot(deg2rad(theta_fine), I_fitted, 'r-', ...
          'LineWidth', 2.5, ...
          'DisplayName', '擬合曲線');

hold on;

polarscatter(deg2rad(theta_deg), I_raw, 45, 'b', 'filled', ...
             'MarkerEdgeColor', 'k', ...
             'DisplayName', '原始量測數據');

title('Malus''s Law 極化圖');

legend('Location', 'bestoutside');

thetaticks(0:30:360);

annotation('textbox', ...
    'Position', [0.60 0.70 0.36 0.08], ...
    'String', text_str, ...
    'Interpreter', 'latex', ...
    'FontSize', 12, ...
    'FontWeight', 'bold', ...
    'BackgroundColor', [1 1 1 0.9], ...
    'EdgeColor', [0.4 0.4 0.4], ...
    'LineWidth', 1, ...
    'HorizontalAlignment', 'left', ...
    'VerticalAlignment', 'top');

%% 步驟 8: 自動儲存兩張圖

figure(fig1);
exportgraphics(fig1, 'MalusLaw_HWP_XY_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

figure(fig2);
exportgraphics(fig2, 'MalusLaw_HWP_Polar_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

disp('兩張圖已儲存到目前工作目錄：');
disp('  1. MalusLaw_HWP_XY_Plot.png');
disp('  2. MalusLaw_HWP_Polar_Plot.png');