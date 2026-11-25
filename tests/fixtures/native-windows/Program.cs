using System;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
class Program {
    [STAThread] static void Main() {
        var app = new Application();
        var w = new Window { Title = "REAlity Counter Fixture", Width = 360, Height = 220 };
        var panel = new StackPanel { Margin = new Thickness(16) };
        var input = new TextBox { Text = "2" };
        AutomationProperties.SetAutomationId(input, "Input");
        var button = new Button { Content = "Double" };
        AutomationProperties.SetAutomationId(button, "Calculate");
        var result = new TextBlock { Text = "Ready" };
        AutomationProperties.SetAutomationId(result, "Result");
        button.Click += (_, _) => result.Text = int.TryParse(input.Text, out int value) ? (value * 2).ToString(System.Globalization.CultureInfo.InvariantCulture) : "Invalid";
        panel.Children.Add(input); panel.Children.Add(button); panel.Children.Add(result); w.Content = panel;
        app.Run(w);
    }
}