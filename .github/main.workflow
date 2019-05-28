workflow "Run tests" {
  resolves = ["test-3.7", "test-3.6", "test-3.5", "test-3.4"]
  on = "push"
}

action "test-3.7" {
  uses = "docker://python:3.7"
  runs = "./test.sh"
  args = "py37"
}

action "test-3.6" {
  uses = "docker://python:3.6"
  runs = "./test.sh"
  args = "py36"
}

action "test-3.5" {
  uses = "docker://python:3.5"
  runs = "./test.sh"
  args = "py35"
}

action "test-3.4" {
  uses = "docker://python:3.4"
  runs = "./test.sh"
  args = "py34"
}
