workflow "Run tests" {
  resolves = ["test"]
  on = "push"
}

action "test" {
  uses = "docker://thekevjames/nox"
  runs = "nox"
}
