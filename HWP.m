clear; clc; close all;

%% 步驟 1: 讀取 Excel 數據
filename = 'polar_data.xlsx';
sheetName = 'HWP';

% 讀取數值數據 (A6:D36，共 36 筆 θ = 0~360°)
data = readmatrix(filename, 'Sheet', sheetName, 'Range', 'A1:D36');

theta_PL2 = data(:, 1);      % 偏振片 PL2 角度
I_data    = data(:, 2:4);    % 三組強度數據

HWP_angles = [30, 45, 60];   % 三組 HWP 角度
numGroups = length(HWP_angles);

disp('數據讀取完成！共 36 筆角度，3 組 HWP 數據。');

%% 步驟 2: 定義擬合模型
% 擬合模型：
% I = I_bg + I0 cos^2(theta_PL2 - theta0)
%
% 理論上：
% theta0 應接近 2*theta_HWP
% 但這裡不畫理論曲線，只用來當初始猜測值與比較

modelFun = @(p, th) p(1) + p(2) .* (cosd(th - p(3))).^2;

options = optimoptions('lsqcurvefit', ...
    'Display', 'off', ...
    'MaxIterations', 500);

%% 步驟 3: 建立儲存擬合結果的變數

p_fit_all = zeros(numGroups, 3);
resnorm_all = zeros(numGroups, 1);
R_squared_all = zeros(numGroups, 1);

theta_fine = 0:0.1:360;
I_fitted_all = zeros(numGroups, length(theta_fine));

%% 步驟 4: 分別對三組數據做擬合

fprintf('=== 擬合結果 ===\n');

for i = 1:numGroups

    I_raw = I_data(:, i);
    theta_HWP = HWP_angles(i);

    % 初始猜測值
    % theta0 初始值使用理論值 2*theta_HWP
    p0 = [min(I_raw), max(I_raw) - min(I_raw), 2*theta_HWP];

    % 非線性擬合
    [p_fit, resnorm] = lsqcurvefit(modelFun, p0, theta_PL2, I_raw, [], [], options);

    I_bg   = p_fit(1);
    I0_fit = p_fit(2);
    theta0 = p_fit(3);

    % 擬合曲線
    I_fitted = modelFun(p_fit, theta_fine);

    % 計算 R^2
    I_pred = modelFun(p_fit, theta_PL2);

    SS_tot = sum((I_raw - mean(I_raw)).^2);
    SS_res = sum((I_raw - I_pred).^2);

    R_squared = 1 - SS_res / SS_tot;

    % 角度差，考慮 cos^2 的 180 度週期
    theta_theory = 2 * theta_HWP;
    theta_diff = mod(theta0 - theta_theory + 90, 180) - 90;

    % 儲存結果
    p_fit_all(i, :) = p_fit;
    resnorm_all(i) = resnorm;
    R_squared_all(i) = R_squared;
    I_fitted_all(i, :) = I_fitted;

    fprintf('\nHWP = %d°\n', theta_HWP);
    fprintf('背景光 I_bg           = %.6f mW\n', I_bg);
    fprintf('振幅 I0_fit           = %.6f mW\n', I0_fit);
    fprintf('擬合角度 theta0       = %.3f °\n', theta0);
    fprintf('理論角度 2θ_HWP       = %.3f °\n', theta_theory);
    fprintf('角度差 theta0 - 2θ_HWP = %.3f °\n', theta_diff);
    fprintf('R^2                   = %.4f\n', R_squared);
    fprintf('殘差平方和            = %.6f\n', resnorm);

end

%% 步驟 5: XY 關係圖

fig1 = figure('Name', 'Malus''s Law - Three HWP Angles', ...
              'Position', [100 100 1100 750]);

hold on;

colors = [
    0.0000 0.4470 0.7410;   % blue
    0.8500 0.3250 0.0980;   % orange
    0.4660 0.6740 0.1880    % green
];

markerTypes = {'o', 's', '^'};

for i = 1:numGroups

    theta_HWP = HWP_angles(i);
    I_raw = I_data(:, i);

    % 原始散佈點
    scatter(theta_PL2, I_raw, 45, colors(i, :), markerTypes{i}, ...
        'filled', ...
        'MarkerFaceAlpha', 0.75, ...
        'MarkerEdgeColor', 'k', ...
        'DisplayName', sprintf('HWP = %d° 原始數據', theta_HWP));

    % 擬合曲線
    plot(theta_fine, I_fitted_all(i, :), '-', ...
        'Color', colors(i, :), ...
        'LineWidth', 2.5, ...
        'DisplayName', sprintf('HWP = %d° 擬合曲線', theta_HWP));

end

grid on;

xlabel('偏振片角度 \theta_{PL2} (degree)');
ylabel('強度 I (mW)');
title('不同 HWP 角度下的 Malus Law 擬合結果');

legend('Location', 'bestoutside');

xlim([0 360]);
ylim([0 max(I_data(:)) * 1.15]);

%% 步驟 6: 加上文字框

text_str = cell(numGroups, 1);

for i = 1:numGroups
    theta_HWP = HWP_angles(i);
    I_bg   = p_fit_all(i, 1);
    I0_fit = p_fit_all(i, 2);
    theta0 = p_fit_all(i, 3);
    R2     = R_squared_all(i);

    text_str{i} = sprintf(['HWP $=%d^\\circ$: $I=%.4g+%.4g\\cos^2' ...
        '(\\theta_{PL2}-%.2f^\\circ)$ mW, $R^2=%.4f$'], ...
        theta_HWP, I_bg*1000, I0_fit*1000, theta0, R2);
end

annotation('textbox', ...
    'Position', [0.15 0.76 0.58 0.13], ...
    'String', text_str, ...
    'Interpreter', 'latex', ...
    'FontSize', 11, ...
    'FontWeight', 'bold', ...
    'BackgroundColor', [1 1 1 0.9], ...
    'EdgeColor', [0.4 0.4 0.4], ...
    'LineWidth', 1, ...
    'HorizontalAlignment', 'left', ...
    'VerticalAlignment', 'top');

%% 步驟 7: 極化圖 Polar Plot

fig2 = figure('Name', 'Malus''s Law - Polar Plot - Three HWP Angles', ...
              'Position', [950 100 850 850]);

polaraxes;
hold on;

for i = 1:numGroups

    theta_HWP = HWP_angles(i);
    I_raw = I_data(:, i);

    % 擬合曲線
    polarplot(deg2rad(theta_fine), I_fitted_all(i, :), '-', ...
        'Color', colors(i, :), ...
        'LineWidth', 2.5, ...
        'DisplayName', sprintf('HWP = %d° 擬合曲線', theta_HWP));

    % 原始數據點
    polarscatter(deg2rad(theta_PL2), I_raw, 45, colors(i, :), ...
        markerTypes{i}, ...
        'filled', ...
        'MarkerEdgeColor', 'k', ...
        'DisplayName', sprintf('HWP = %d° 原始數據', theta_HWP));

end

title('不同 HWP 角度下的 Malus Law 極化圖');

legend('Location', 'bestoutside');

thetaticks(0:30:360);


%% 步驟 8: 自動儲存兩張圖

figure(fig1);
exportgraphics(fig1, 'MalusLaw_ThreeHWP_XY_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

figure(fig2);
exportgraphics(fig2, 'MalusLaw_ThreeHWP_Polar_Plot.png', ...
    'Resolution', 300, ...
    'ContentType', 'image');

disp('兩張圖已儲存到目前工作目錄：');
disp('  1. MalusLaw_ThreeHWP_XY_Plot.png');
disp('  2. MalusLaw_ThreeHWP_Polar_Plot.png');